"""Announcement endpoints for the High School Management System API"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from ..database import announcements_collection, teachers_collection

router = APIRouter(
	prefix="/announcements",
	tags=["announcements"]
)


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
	if not teacher_username:
		raise HTTPException(status_code=401, detail="Authentication required for this action")

	teacher = teachers_collection.find_one({"_id": teacher_username})
	if not teacher:
		raise HTTPException(status_code=401, detail="Invalid teacher credentials")

	return teacher


def _parse_date(value: Optional[str], field_name: str, required: bool = False) -> Optional[date]:
	if value in (None, ""):
		if required:
			raise HTTPException(status_code=400, detail=f"{field_name} is required")
		return None

	try:
		return date.fromisoformat(value)
	except ValueError as exc:
		raise HTTPException(
			status_code=400,
			detail=f"{field_name} must use YYYY-MM-DD format"
		) from exc


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"id": str(doc["_id"]),
		"message": doc.get("message", ""),
		"start_date": doc.get("start_date"),
		"expiration_date": doc.get("expiration_date"),
		"created_by": doc.get("created_by"),
		"created_at": doc.get("created_at")
	}


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
	"""Get all currently active announcements for public display."""
	today = date.today().isoformat()

	query = {
		"expiration_date": {"$gte": today},
		"$or": [
			{"start_date": None},
			{"start_date": ""},
			{"start_date": {"$exists": False}},
			{"start_date": {"$lte": today}}
		]
	}

	announcements = announcements_collection.find(query).sort(
		[("expiration_date", 1), ("created_at", -1)]
	)

	return [_serialize_announcement(doc) for doc in announcements]


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
	"""Get all announcements for management; requires authentication."""
	_require_signed_in_user(teacher_username)

	announcements = announcements_collection.find().sort(
		[("expiration_date", 1), ("created_at", -1)]
	)

	return [_serialize_announcement(doc) for doc in announcements]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
	message: str,
	expiration_date: str,
	start_date: Optional[str] = None,
	teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
	"""Create a new announcement; requires authentication."""
	teacher = _require_signed_in_user(teacher_username)

	cleaned_message = (message or "").strip()
	if not cleaned_message:
		raise HTTPException(status_code=400, detail="message is required")

	parsed_start_date = _parse_date(start_date, "start_date", required=False)
	parsed_expiration_date = _parse_date(expiration_date, "expiration_date", required=True)

	if parsed_start_date and parsed_start_date > parsed_expiration_date:
		raise HTTPException(status_code=400, detail="start_date cannot be after expiration_date")

	now = datetime.utcnow().isoformat() + "Z"
	doc = {
		"message": cleaned_message,
		"start_date": parsed_start_date.isoformat() if parsed_start_date else None,
		"expiration_date": parsed_expiration_date.isoformat(),
		"created_by": teacher["username"],
		"created_at": now
	}

	result = announcements_collection.insert_one(doc)
	created = announcements_collection.find_one({"_id": result.inserted_id})

	if not created:
		raise HTTPException(status_code=500, detail="Failed to create announcement")

	return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
	announcement_id: str,
	message: str,
	expiration_date: str,
	start_date: Optional[str] = None,
	teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
	"""Update an existing announcement; requires authentication."""
	_require_signed_in_user(teacher_username)

	cleaned_message = (message or "").strip()
	if not cleaned_message:
		raise HTTPException(status_code=400, detail="message is required")

	parsed_start_date = _parse_date(start_date, "start_date", required=False)
	parsed_expiration_date = _parse_date(expiration_date, "expiration_date", required=True)

	if parsed_start_date and parsed_start_date > parsed_expiration_date:
		raise HTTPException(status_code=400, detail="start_date cannot be after expiration_date")

	try:
		object_id = ObjectId(announcement_id)
	except Exception as exc:
		raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

	result = announcements_collection.update_one(
		{"_id": object_id},
		{
			"$set": {
				"message": cleaned_message,
				"start_date": parsed_start_date.isoformat() if parsed_start_date else None,
				"expiration_date": parsed_expiration_date.isoformat(),
			}
		}
	)

	if result.matched_count == 0:
		raise HTTPException(status_code=404, detail="Announcement not found")

	updated = announcements_collection.find_one({"_id": object_id})
	if not updated:
		raise HTTPException(status_code=500, detail="Failed to update announcement")

	return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
	announcement_id: str,
	teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
	"""Delete an announcement; requires authentication."""
	_require_signed_in_user(teacher_username)

	try:
		object_id = ObjectId(announcement_id)
	except Exception as exc:
		raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

	result = announcements_collection.delete_one({"_id": object_id})
	if result.deleted_count == 0:
		raise HTTPException(status_code=404, detail="Announcement not found")

	return {"message": "Announcement deleted"}
