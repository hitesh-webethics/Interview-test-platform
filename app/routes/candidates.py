from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user, require_admin
import json


router = APIRouter(prefix="/candidates", tags=["Candidates"])


def format_time(seconds: int) -> str:
    """Convert seconds to MM:SS format or Xs format"""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

# ============================================
# SUBMIT TEST (Public - No Auth Required)
# ============================================
@router.post("/submit", response_model=schemas.CandidateResponse)
def submit_test(
    submission: schemas.CandidateCreate,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for candidates to submit their completed test.
    
    Creates:
    1. One Candidate entry (basic info)
    2. One Response entry (all answers + validation)
    """
    
    # Validate name is not empty
    if not submission.name.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "'name' cannot be empty"
            }
        )
    
    # Find test by test_code (testId from frontend)
    test = db.query(models.Test).filter(
        models.Test.test_code == submission.testId
    ).first()
    
    if not test:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "error": "Invalid test code"
            }
        )
    
    # Parse test questions data
    questions_data = json.loads(test.questions_data)
    
    # Validate answer count matches question count
    if len(submission.answers) != len(questions_data):
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": f"Expected {len(questions_data)} answers, received {len(submission.answers)}"
            }
        )
    
    # Create candidate record first
    db_candidate = models.Candidate(
        name=submission.name,
        email=submission.email,
        test_id=test.id,
        time_taken=submission.timeTaken
    )
    
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    # Create a mapping of question_id to question data for faster lookup
    questions_map = {str(q["question_id"]): q for q in questions_data}
    
    # Validate and build answers array with results
    validated_answers = []
    correct_count = 0
    
    for answer_item in submission.answers:
        question_id = answer_item.questionId
        selected_option = answer_item.selected.upper()  # Ensure uppercase
        
        # Find the question in test data
        question = questions_map.get(str(question_id))
        
        if not question:
            # Rollback if any question is invalid
            db.delete(db_candidate)
            db.commit()
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": f"Question ID '{question_id}' not found in test"
                }
            )
        
        # Check if answer is correct (case-insensitive comparison)
        correct_answer = question["answer"].upper()
        is_correct = (selected_option == correct_answer)
        
        if is_correct:
            correct_count += 1
        
        # Add to validated answers array
        validated_answers.append({
            "questionId": question_id,
            "selected": selected_option,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })
    
    # Create single response record with all answers
    db_response = models.Response(
        candidate_id=db_candidate.id,
        test_id=test.id,
        answers=json.dumps(validated_answers),  # Store as JSON string
        is_correct=correct_count
    )
    
    db.add(db_response)
    db.commit()
    
    return db_candidate


# ============================================
# GET CANDIDATE RESULT BY ID (Public - No Auth)
# ============================================
@router.get("/result/{candidate_id}", response_model=schemas.CandidateResultResponse)
def get_candidate_result(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a specific candidate.
    Shows full breakdown of all answers with correct/incorrect status.
    Public endpoint - anyone with candidate_id can view (shared via link).
    """
    
    # Get candidate
    candidate = db.query(models.Candidate).filter(
        models.Candidate.id == candidate_id
    ).first()
    
    if not candidate:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "error": "Candidate not found"
            }
        )
    
    # Get response record
    response = db.query(models.Response).filter(
        models.Response.candidate_id == candidate_id
    ).first()
    
    if not response:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "error": "Response not found"
            }
        )
    
    # Get test and questions data
    test = db.query(models.Test).filter(models.Test.id == candidate.test_id).first()
    questions_data = json.loads(test.questions_data)
    questions_map = {str(q["question_id"]): q for q in questions_data}
    
    # Parse answers from response
    answers = json.loads(response.answers)
    
    # Calculate score
    total_questions = len(answers)
    correct_answers = response.is_correct
    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Build detailed question breakdown
    question_breakdown = []
    for answer in answers:
        question = questions_map.get(answer["questionId"])
        
        if question:
            question_breakdown.append(schemas.QuestionBreakdown(
                question_id=answer["questionId"],
                question_text=question["question"],
                selected_option=answer["selected"],
                correct_option=answer["correct_answer"],
                is_correct=answer["is_correct"],
                options=question["options"],
                difficulty=question.get("difficulty", "Medium"),
                category_name=question["category"]["name"],
                subcategory_name=question["category"].get("subcategory")
            ))
    
    # Build candidate detail response
    candidate_detail = schemas.CandidateDetailResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        test_id=candidate.test_id,
        test_code=test.test_code,
        time_taken=candidate.time_taken,
        time_taken_formatted=format_time(candidate.time_taken),
        total_questions=total_questions,
        correct_answers=correct_answers,
        score=round(score_percentage, 2),
        created_at=candidate.created_at
    )
    
    return schemas.CandidateResultResponse(
        candidate=candidate_detail,
        responses=question_breakdown  # Changed from response_details
    )


# ============================================
# GET ALL RESULTS (Admin/Creator Dashboard)
# ============================================
@router.get("/results", response_model=List[schemas.CandidateListItem])
def get_all_results(
    test_code: Optional[str] = Query(None, description="Filter by test code"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all candidate results for dashboard.
    Supports filtering by test_code.
    Only accessible by authenticated users (Admin/Creator).
    """
    
    # Start with base query
    query = db.query(models.Candidate)
    
    # Apply test_code filter if provided
    if test_code:
        test = db.query(models.Test).filter(
            models.Test.test_code == test_code
        ).first()
        
        if not test:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "error": "Test not found"
                }
            )
        
        query = query.filter(models.Candidate.test_id == test.id)
    
    # Get all candidates
    candidates = query.order_by(models.Candidate.created_at.desc()).all()
    
    # Build response list with scores
    result = []
    for candidate in candidates:
        # Get test info
        test = db.query(models.Test).filter(models.Test.id == candidate.test_id).first()
        
        # Get response (single entry)
        response = db.query(models.Response).filter(
            models.Response.candidate_id == candidate.id
        ).first()
        
        if response:
            answers = json.loads(response.answers)
            total_questions = len(answers)
            correct_answers = response.is_correct
            score_percentage = int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
            
            result.append(schemas.CandidateListItem(
                id=candidate.id,
                name=candidate.name,
                email=candidate.email,
                test_code=test.test_code,
                score=f"{correct_answers}/{total_questions}",
                score_percentage=score_percentage,
                time_taken_formatted=format_time(candidate.time_taken),
                created_at=candidate.created_at
            ))
    
    return result