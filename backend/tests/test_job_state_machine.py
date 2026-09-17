import pytest
from app.schemas.job import JobStatus
from app.services.job_service import job_service, InvalidStateTransitionError

def test_valid_transitions():
    # QUEUED -> PROCESSING
    job_service._validate_transition(JobStatus.QUEUED, JobStatus.PROCESSING)
    # PROCESSING -> COMPLETED
    job_service._validate_transition(JobStatus.PROCESSING, JobStatus.COMPLETED)
    # PROCESSING -> FAILED
    job_service._validate_transition(JobStatus.PROCESSING, JobStatus.FAILED)
    # COMPLETED -> EXPIRED
    job_service._validate_transition(JobStatus.COMPLETED, JobStatus.EXPIRED)
    # QUEUED -> CANCELLED
    job_service._validate_transition(JobStatus.QUEUED, JobStatus.CANCELLED)

def test_invalid_transitions():
    # COMPLETED -> PROCESSING is illegal
    with pytest.raises(InvalidStateTransitionError):
        job_service._validate_transition(JobStatus.COMPLETED, JobStatus.PROCESSING)

    # FAILED -> COMPLETED is illegal
    with pytest.raises(InvalidStateTransitionError):
        job_service._validate_transition(JobStatus.FAILED, JobStatus.COMPLETED)

    # QUEUED -> EXPIRED is illegal
    with pytest.raises(InvalidStateTransitionError):
        job_service._validate_transition(JobStatus.QUEUED, JobStatus.EXPIRED)
