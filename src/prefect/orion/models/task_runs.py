from typing import List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import delete, select

from prefect.orion import models, schemas
from prefect.orion.models import orm


async def create_task_run(
    session: sa.orm.Session, task_run: schemas.core.TaskRun
) -> orm.TaskRun:
    """Creates a new task run. If the provided task run has a state attached, it
    will also be created.

    Args:
        session (sa.orm.Session): a database session
        task_run (schemas.core.TaskRun): a task run model

    Returns:
        orm.TaskRun: the newly-created flow run
    """
    model = orm.TaskRun(**task_run.dict(shallow=True, exclude={"state"}), state=None)
    session.add(model)
    await session.flush()
    if task_run.state:
        await models.task_run_states.orchestrate_task_run_state(
            session=session, task_run_id=model.id, state=task_run.state
        )
    return model


async def read_task_run(session: sa.orm.Session, task_run_id: UUID) -> orm.TaskRun:
    """Read a task run by id

    Args:
        session (sa.orm.Session): a database session
        task_run_id (str): the task run id

    Returns:
        orm.TaskRun: the task run
    """
    model = await session.get(orm.TaskRun, task_run_id)
    return model


async def read_task_runs(
    session: sa.orm.Session, flow_run_id: UUID
) -> List[orm.TaskRun]:
    """Read a task runs asssociated with a flow run

    Args:
        session (sa.orm.Session): a database session
        flow_run_id (str): the flow run id

    Returns:
        List[orm.TaskRun]: the task runs
    """
    query = (
        select(orm.TaskRun)
        .filter(orm.TaskRun.flow_run_id == flow_run_id)
        .order_by(orm.TaskRun.id)
    )
    result = await session.execute(query)
    return result.scalars().unique().all()


async def delete_task_run(session: sa.orm.Session, task_run_id: UUID) -> bool:
    """Delete a task run by id

    Args:
        session (sa.orm.Session): a database session
        task_run_id (str): the task run id to delete

    Returns:
        bool: whether or not the task run was deleted
    """
    result = await session.execute(
        delete(orm.TaskRun).where(orm.TaskRun.id == task_run_id)
    )
    return result.rowcount > 0
