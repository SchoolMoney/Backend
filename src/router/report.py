from fastapi import APIRouter, logger
import src.SQL as SQL
from src.SQL.Enum import CollectionOperationType
from src.Service import Auth
from src.repository import collection_repository
from datetime import date
from typing import Annotated
from fastapi import Depends, HTTPException, status
from src.Service.Collection.collection_validator import (
    check_if_user_can_view_collection,
)

report_router = APIRouter()


@report_router.get("/financial/collection", status_code=status.HTTP_200_OK)
async def generate_financial_report(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        collection_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    """Generate a financial report with collection details and payment status"""
    try:
        collection = await collection_repository.get_by_id(sql_session, collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection with ID {collection_id} not found"
            )

        can_view = await check_if_user_can_view_collection(
            sql_session, collection_id, user.user_id,
        )
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this collection's data"
            )

        # Get children data for the collection
        children_data = await collection_repository.get_list_of_children_for_collection(
            session=sql_session,
            collection_id=collection_id
        )

        # Get payment operations for children in this collection
        query = SQL.select(SQL.Tables.CollectionOperation).where(
            SQL.Tables.CollectionOperation.collection_id == collection_id,
            SQL.Tables.CollectionOperation.operation_type == CollectionOperationType.PAY
        )
        result = await sql_session.exec(query)
        payment_operations = result.all()

        paid_child_ids = {op.child_id for op in payment_operations}

        paid_children = []
        unpaid_children = []

        for child in children_data:
            child_info = {
                "child_id": child.child_id,
                "child_name": child.child_name,
                "child_surname": child.child_surname,
            }

            if child.child_id in paid_child_ids:
                paid_children.append(child_info)
            else:
                unpaid_children.append(child_info)

        total_expected = collection.price * len(children_data)
        total_collected = collection.price * len(paid_children)

        financial_report = {
            "collection_info": {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "start_date": collection.start_date.isoformat(),
                "end_date": collection.end_date.isoformat() if collection.end_date else None,
                "price_per_child": collection.price,
                "status": collection.status,
            },
            "financial_summary": {
                "total_children": len(children_data),
                "paid_children_count": len(paid_children),
                "unpaid_children_count": len(unpaid_children),
                "total_expected": total_expected,
                "total_collected": total_collected,
                "outstanding_amount": total_expected - total_collected,
                "withdrawn_money": collection.withdrawn_money,
                "available_balance": total_collected - collection.withdrawn_money,
            },
            "paid_children": paid_children,
            "unpaid_children": unpaid_children,
            "generated_date": date.today().isoformat()
        }

        return financial_report
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Error generating financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate financial report"
        )
