from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas
from app.database import get_db
from app.auth import require_admin, require_creator_or_admin
import json

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def format_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


# SUBMIT TEST (Public - No Auth)
@router.post("/submit")
def submit_test(
    submission: schemas.CandidateCreate,
    db: Session = Depends(get_db)
):  
    # Validation 1: Name cannot be empty
    if not submission.name or not submission.name.strip():
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "'name' cannot be empty"
            }
        )
    
    # Validation 2: Test code must exist
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
    
    # Get test questions
    questions_data = json.loads(test.questions_data)
    total_questions = len(questions_data)
    
    # Validation 3: Must answer ALL questions
    if len(submission.answers) != total_questions:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": f"You must answer all {total_questions} questions. You answered {len(submission.answers)}"
            }
        )
    
    # Validation 4: Every answer must have a selected option (not empty)
    for idx, answer in enumerate(submission.answers, start=1):
        if not answer.selected or not answer.selected.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": f"Question {idx} has no answer selected. All questions must be answered."
                }
            )
    
    # Check if candidate already exists by email
    db_candidate = db.query(models.Candidate).filter(
        models.Candidate.email == submission.email
    ).first()
    
    # If candidate doesn't exist, create new one
    if not db_candidate:
        db_candidate = models.Candidate(
            name=submission.name.strip(),
            email=submission.email
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
    
    # All validations passed - Process answers and check correctness
    questions_map = {str(q["question_id"]): q for q in questions_data}
    validated_answers = []
    correct_count = 0
    
    for answer_item in submission.answers:
        question_id = str(answer_item.questionId)
        selected_option = answer_item.selected.strip().upper()
        
        # Get question from test data
        question = questions_map.get(question_id)
        
        if question:
            # Check if answer is correct
            correct_answer = question["answer"].upper()
            is_correct = (selected_option == correct_answer)
            
            if is_correct:
                correct_count += 1
            
            validated_answers.append({
                "questionId": question_id,
                "selected": selected_option,
                "correct": correct_answer,
                "isCorrect": is_correct
            })
    
    # Create response record with all answers as JSON and time_taken
    db_response = models.Response(
        candidate_id=db_candidate.id,
        test_id=test.id,
        answers=json.dumps(validated_answers),
        score=correct_count,
        time_taken=submission.timeTaken
    )
    
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    # Return success response with candidate details
    return JSONResponse(
        status_code=200,
        content={
            "message": "Test Submitted Successfully!",
            "thank_you_message": f"Thank you for completing the test, {db_candidate.name}",
            "response": {
                "id": db_response.id,
                "candidate_id": db_candidate.id,
                "name": db_candidate.name,
                "email": db_candidate.email,
                "test_code": test.test_code,
                "time_taken": db_response.time_taken,
                "score": f"{correct_count}/{len(validated_answers)}",
                "answered_at": db_response.answered_at.isoformat()
            }
        }
    )


# GET RESULT BY CANDIDATE ID (Admin/Creator Only)
@router.get("/result/{candidate_id}", response_model=schemas.CandidateResultResponse)
def get_candidate_result(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator_or_admin)
):

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
                "error": "Response data not found for this candidate"
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
    correct_answers = response.score
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
                correct_option=answer["correct"],
                is_correct=answer["isCorrect"],
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
        test_id=response.test_id,  # From response table
        test_code=test.test_code,
        time_taken=response.time_taken,  # Now from response table
        time_taken_formatted=format_time(response.time_taken),
        total_questions=total_questions,
        correct_answers=correct_answers,
        score=round(score_percentage, 2),
        created_at=response.answered_at  # Use response timestamp
    )
    
    return schemas.CandidateResultResponse(
        candidate=candidate_detail,
        responses=question_breakdown
    )

# GET ALL RESULTS (Admin/Creator Only)
@router.get("/results", response_model=List[schemas.CandidateListItem])
def get_all_results(
    test_code: Optional[str] = Query(None, description="Filter by test code"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_creator_or_admin)
):
    # Query responses instead of candidates
    query = db.query(models.Response)
    
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
        
        query = query.filter(models.Response.test_id == test.id)
    
    # Get all responses (most recent first)
    responses = query.order_by(models.Response.answered_at.desc()).all()
    
    # Build response list
    result = []
    for response in responses:
        candidate = db.query(models.Candidate).filter(
            models.Candidate.id == response.candidate_id
        ).first()
        
        test = db.query(models.Test).filter(
            models.Test.id == response.test_id
        ).first()
        
        answers = json.loads(response.answers)
        total_questions = len(answers)
        correct_answers = response.score
        score_percentage = int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
        
        result.append(schemas.CandidateListItem(
            id=response.id,  # Now showing response ID
            name=candidate.name,
            email=candidate.email,
            test_code=test.test_code,
            score=f"{correct_answers}/{total_questions}",
            score_percentage=score_percentage,
            time_taken_formatted=format_time(response.time_taken),
            created_at=response.answered_at
        ))
    
    return result

# DELETE CANDIDATE (Admin Only)
@router.delete("/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    
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
    
    # Delete response first (manually)
    db.query(models.Response).filter(
        models.Response.candidate_id == candidate_id
    ).delete()
    
    # Then delete candidate
    db.delete(candidate)
    db.commit()
    
    return {"message": "Candidate and their responses deleted successfully"}

# DELETE RESPONSE BY ID (Admin Only)
@router.delete("/response/{response_id}")
def delete_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    
    response = db.query(models.Response).filter(
        models.Response.id == response_id
    ).first()
    
    if not response:
        return JSONResponse(
            status_code=404,
            content={
                "status": 404,
                "error": "Response not found"
            }
        )
    
    # Delete the response
    db.delete(response)
    db.commit()
    
    return {"message": "Response deleted successfully"}