"""
Task services — identical logic, parameterised by model class.

Each database backend gets the same CRUD operations so you can compare
behaviour side-by-side from Swagger UI.
"""

from __future__ import annotations

import uuid

from app.utils.status_code import StatusCode


class TaskService:
    """
    Generic CRUD service for any async ``BaseDocument`` subclass.

    Instantiate once per backend:

        pg_service = TaskService(TaskPg, "PostgreSQL", logger)
    """

    def __init__(self, model, backend_label: str, logger):
        self.model = model
        self.label = backend_label
        self.logger = logger

    async def create_task(self, data: dict = None):
        try:
            task_id = str(uuid.uuid4())
            await self.model.insert_one({
                "task_id": task_id,
                "title": data["title"],
                "description": data["description"],
                "status": data["status"],
                "assignee": data["assignee"],
            })
            self.logger.success(f"[{self.label}] Task '{data['title']}' created successfully")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = {
                "task_id": task_id,
                "backend": self.label,
                "message": f"Task '{data['title']}' created successfully",
            }
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def get_task(self, task_id: str = None):
        try:
            task = await self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.response()
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
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def get_all_tasks(self):
        try:
            tasks = await self.model.find({})
            if not tasks["status"]:
                self.logger.error(f"[{self.label}] Failed to retrieve tasks")
                status = StatusCode.FIND_ITEM_ERROR.response()
                status["content"]["detail"] = "Failed to retrieve tasks"
                return status
            result = tasks["result"]
            if isinstance(result, list):
                for r in result:
                    if isinstance(r, dict):
                        r.pop("_id", None)
            self.logger.success(f"[{self.label}] Found {len(result)} tasks")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def get_tasks_by_assignee(self, assignee: str = None):
        try:
            tasks = await self.model.find({"assignee": assignee})
            if not tasks["status"]:
                self.logger.error(f"[{self.label}] Failed to retrieve tasks for {assignee}")
                status = StatusCode.FIND_ITEM_ERROR.response()
                status["content"]["detail"] = f"Failed to retrieve tasks for {assignee}"
                return status
            result = tasks["result"]
            if isinstance(result, list):
                for r in result:
                    if isinstance(r, dict):
                        r.pop("_id", None)
            self.logger.success(f"[{self.label}] Found {len(result)} tasks for {assignee}")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def update_task(self, task_id: str = None, data: dict = None):
        try:
            task = await self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.response()
                status["content"]["detail"] = f"Task {task_id} not found"
                return status
            update_data = {k: v for k, v in data.items() if v is not None}
            if not update_data:
                status = StatusCode.SUCCESS.response()
                status["content"]["detail"] = "No fields to update"
                return status
            await self.model.update_one({"task_id": task_id}, update_data)
            self.logger.success(f"[{self.label}] Task {task_id} updated successfully")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = f"Task {task_id} updated successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status

    async def delete_task(self, task_id: str = None):
        try:
            task = await self.model.find_one({"task_id": task_id})
            if not task["status"] or len(task["result"]) == 0:
                self.logger.error(f"[{self.label}] Task {task_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.response()
                status["content"]["detail"] = f"Task {task_id} not found"
                return status
            result = await self.model.delete_one({"task_id": task_id})
            if not result["status"]:
                self.logger.error(f"[{self.label}] {result.get('error', 'Unknown error')}")
                status = StatusCode.UNKNOWN_ERROR.response()
                status["content"]["detail"] = result.get("error", "Unknown error")
                return status
            self.logger.success(f"[{self.label}] Task {task_id} deleted successfully")
            status = StatusCode.SUCCESS.response()
            status["content"]["detail"] = f"Task {task_id} deleted successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.response()
            status["content"]["detail"] = str(e)
            return status
