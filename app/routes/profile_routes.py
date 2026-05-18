from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas import UserProfileRequest, UserProfileResponse
from app.services.profile_service import ProfileService
from app.core.security import get_current_user

router = APIRouter()


@router.post("", response_model=UserProfileResponse)
def create_profile(
    profile_data: UserProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new health profile for the current user.
    
    Args:
        profile_data: Profile data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created profile
    """
    user_id = UUID(current_user.get("user_id"))
    profile = ProfileService.create_profile(db, user_id, profile_data)
    response = UserProfileResponse.model_validate(profile).model_dump()
    response["message"] = "User profile created successfully"
    return response


@router.get("", response_model=list[UserProfileResponse])
def get_user_profiles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all profiles for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of user profiles
    """
    user_id = UUID(current_user.get("user_id"))
    profiles = ProfileService.get_user_profiles(db, user_id)
    return profiles


@router.get("/latest", response_model=UserProfileResponse)
def get_latest_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent profile for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Latest profile
    """
    user_id = UUID(current_user.get("user_id"))
    profile = ProfileService.get_latest_profile(db, user_id)
    return profile


@router.get("/{profile_id}", response_model=UserProfileResponse)
def get_profile(
    profile_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific profile by ID.
    
    Args:
        profile_id: Profile ID to retrieve
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Profile data
    """
    user_id = UUID(current_user.get("user_id"))
    profile = ProfileService.get_profile(db, user_id, profile_id)
    return profile


@router.put("/{profile_id}", response_model=UserProfileResponse)
def update_profile(
    profile_id: UUID,
    profile_data: UserProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing profile.
    
    Args:
        profile_id: Profile ID to update
        profile_data: New profile data
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Updated profile
    """
    user_id = UUID(current_user.get("user_id"))
    profile = ProfileService.update_profile(db, user_id, profile_id, profile_data)
    return profile
