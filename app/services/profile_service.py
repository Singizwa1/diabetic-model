from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from app.models import UserProfile, User
from app.schemas import UserProfileRequest, UserProfileResponse


class ProfileService:
    """Service for managing user health profiles."""
    
    @staticmethod
    def create_profile(db: Session, user_id: UUID, profile_data: UserProfileRequest) -> UserProfile:
        """
        Create a new profile for a user.
        
        Args:
            db: Database session
            user_id: User ID
            profile_data: Profile data
        
        Returns:
            Created profile
        
        Raises:
            HTTPException: If user not found
        """
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate BMI
        bmi = ProfileService._calculate_bmi(profile_data.height_cm, profile_data.weight_kg)
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            age=profile_data.age,
            sex=profile_data.sex,
            height_cm=profile_data.height_cm,
            weight_kg=profile_data.weight_kg,
            bmi=bmi
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    @staticmethod
    def update_profile(db: Session, user_id: UUID, profile_id: UUID, profile_data: UserProfileRequest) -> UserProfile:
        """
        Update an existing profile.
        
        Args:
            db: Database session
            user_id: User ID (for authorization)
            profile_id: Profile ID to update
            profile_data: New profile data
        
        Returns:
            Updated profile
        
        Raises:
            HTTPException: If profile not found or not authorized
        """
        profile = db.query(UserProfile).filter(
            UserProfile.id == profile_id,
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Update fields
        profile.age = profile_data.age
        profile.sex = profile_data.sex
        profile.height_cm = profile_data.height_cm
        profile.weight_kg = profile_data.weight_kg
        profile.bmi = ProfileService._calculate_bmi(profile_data.height_cm, profile_data.weight_kg)
        
        db.commit()
        db.refresh(profile)
        return profile
    
    @staticmethod
    def get_user_profiles(db: Session, user_id: UUID) -> list[UserProfile]:
        """Get all profiles for a user."""
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).all()
    
    @staticmethod
    def get_latest_profile(db: Session, user_id: UUID) -> UserProfile:
        """Get the most recent profile for a user."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).order_by(UserProfile.created_at.desc()).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No profile found for user"
            )
        return profile
    
    @staticmethod
    def _calculate_bmi(height_cm: float, weight_kg: float) -> float:
        """
        Calculate BMI from height and weight.
        
        Args:
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
        
        Returns:
            BMI value
        """
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
