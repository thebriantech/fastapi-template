"""
Task services — identical logic, parameterised by model class.

Each database backend gets the same CRUD operations so you can compare
behaviour side-by-side from Swagger UI.
"""

from __future__ import annotations

import uuid
from typing import Type

from app.db.base_document import BaseDocument
from app.utils.status_code import StatusCode


class TaskService:
    """
    Generic CRUD service that works with **any** ``BaseDocument`` subclass.

    Instantiate once per backend:

        pg_service = TaskService(TaskPg, "PostgreSQL", logger)
    """

    def __init__(self, model: Type[BaseDocument], backend_label: str, logger):
        self.model = model
        self.label = backend_label
        self.logger = logger

    def create_task(self, data: dict = None):
        try:
            task_id = str(uuid.uuid4())
            self.model.insert_one({
                "task_id": task_id,
                "title": data["title"],
                "description": data["description"],
                "status": data["status"],
                "assignee": data["assignee"],
            })
            self.logger.success(f"[{self.label}] Task '{data['title']}' created successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = {
                "task_id": task_id,
                "backend": self.label,
                "message": f"Task '{data['title']}' created successfully",
            }
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def get_task(self, task_id: str = None):
        try:
            task = self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Task {task_id} not found"
                return status
            result = task["result"]
            if isinstance(result, dict):
                result.pop("_id", None)
            elif isinstance(result, list):
                for r in result:
                    if isinstance(r, dict):
                        r.pop("_id", None)
            self.logger.success(f"[{self.label}] Task {task_id} found")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def get_all_tasks(self):
        try:
            tasks = self.model.find({})
            if not tasks["status"]:
                self.logger.error(f"[{self.label}] Failed to retrieve tasks")
                status = StatusCode.FIND_ITEM_ERROR.value
                status["content"]["detail"] = "Failed to retrieve tasks"
                return status
            result = tasks["result"]
            if isinstance(result, list):
                for r in result:
                    if isinstance(r, dict):
                        r.pop("_id", None)
            self.logger.success(f"[{self.label}] Found {len(result)} tasks")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def get_tasks_by_assignee(self, assignee: str = None):
        try:
            tasks = self.model.find({"assignee": assignee})
            if not tasks["status"]:
                self.logger.error(f"[{self.label}] Failed to retrieve tasks for {assignee}")
                status = StatusCode.FIND_ITEM_ERROR.value
                status["content"]["detail"] = f"Failed to retrieve tasks for {assignee}"
                return status
            result = tasks["result"]
            if isinstance(result, list):
                for r in result:
                    if isinstance(r, dict):
                        r.pop("_id", None)
            self.logger.success(f"[{self.label}] Found {len(result)} tasks for {assignee}")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def update_task(self, task_id: str = None, data: dict = None):
        try:
            task = self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Task {task_id} not found"
                return status
            update_data = {k: v for k, v in data.items() if v is not None}
            if not update_data:
                status = StatusCode.SUCCESS.value
                status["content"]["detail"] = "No fields to update"
                return status
            self.model.update_one({"task_id": task_id}, update_data)
            self.logger.success(f"[{self.label}] Task {task_id} updated successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = f"Task {task_id} updated successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def delete_task(self, task_id: str = None):
        try:
            task = self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Task {task_id} not found"
                return status
            result = self.model.delete_one({"task_id": task_id})
            if not result["status"]:
                self.logger.error(f"[{self.label}] {result['error']}")
                status = StatusCode.UNKNOWN_ERROR.value
                status["content"]["detail"] = result["error"]
                return status
            self.logger.success(f"[{self.label}] Task {task_id} deleted successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = f"Task {task_id} deleted successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status
