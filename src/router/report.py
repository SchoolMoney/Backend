from fastapi import APIRouter, logger
import src.SQL as SQL
from src.SQL.Enum import CollectionOperationType
from src.Model.UserAccountPrivilegeEnum import UserAccountPrivilegeEnum
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
    try:
        collection = await collection_repository.get_by_id(sql_session, collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection with ID {collection_id} not found",
            )

        if user.user_privilege == UserAccountPrivilegeEnum.ADMIN_USER:
            can_view = True
        else:
            can_view = await check_if_user_can_view_collection(
                sql_session,
                collection_id,
                user.user_id,
            )

        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this collection's data",
            )

        children_data = await collection_repository.get_list_of_children_for_collection(
            session=sql_session, collection_id=collection_id
        )

        query = SQL.select(SQL.Tables.CollectionOperation).where(
            SQL.Tables.CollectionOperation.collection_id == collection_id,
            SQL.Tables.CollectionOperation.operation_type
            == CollectionOperationType.PAY,
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
                "end_date": (
                    collection.end_date.isoformat() if collection.end_date else None
                ),
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
                "available_balance": total_collected - collection.withdrawn_money if total_collected - collection.withdrawn_money >= 0  else 0,
            },
            "paid_children": paid_children,
            "unpaid_children": unpaid_children,
            "generated_date": date.today().isoformat(),
        }

        return financial_report
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Error generating financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate financial report",
        )


@report_router.get("/financial/class", status_code=status.HTTP_200_OK)
async def generate_class_financial_report(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        class_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    try:
        query = SQL.select(SQL.Tables.Collection).where(
            SQL.Tables.Collection.class_group_id == class_id
        )
        result = await sql_session.exec(query)
        collections = result.all()

        if not collections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No collections found for class ID {class_id}"
            )

        class_query = SQL.select(SQL.Tables.ClassGroup).where(
            SQL.Tables.ClassGroup.id == class_id
        )
        class_result = await sql_session.exec(class_query)
        class_data = class_result.first()

        if not class_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with ID {class_id} not found"
            )

        # Get all children in the class
        children_query = SQL.select(SQL.Tables.Child).where(
            SQL.Tables.Child.group_id == class_id
        )
        children_result = await sql_session.exec(children_query)
        children = children_result.all()

        # Initialize report data
        collections_summary = []
        total_expected = 0
        total_collected = 0
        total_withdrawn = 0

        # Process each collection
        for collection in collections:
            # Get payment operations for this collection
            payment_query = SQL.select(SQL.Tables.CollectionOperation).where(
                SQL.Tables.CollectionOperation.collection_id == collection.id,
                SQL.Tables.CollectionOperation.operation_type == CollectionOperationType.PAY,
            )
            payment_result = await sql_session.exec(payment_query)
            payments = payment_result.all()

            # Calculate collection-specific totals
            paid_count = len(payments)
            expected_amount = collection.price * len(children)
            collected_amount = collection.price * paid_count

            # Add to overall totals
            total_expected += expected_amount
            total_collected += collected_amount
            total_withdrawn += collection.withdrawn_money

            # Add collection summary
            collections_summary.append({
                "id": collection.id,
                "name": collection.name,
                "start_date": collection.start_date.isoformat(),
                "end_date": collection.end_date.isoformat() if collection.end_date else None,
                "price_per_child": collection.price,
                "status": collection.status,
                "total_children": len(children),
                "paid_children": paid_count,
                "unpaid_children": len(children) - paid_count,
                "expected_amount": expected_amount,
                "collected_amount": collected_amount,
                "outstanding_amount": expected_amount - collected_amount,
                "withdrawn_money": collection.withdrawn_money,
                "available_balance": collected_amount - collection.withdrawn_money,
            })

        # Prepare the final report
        class_report = {
            "class_info": {
                "id": class_data.id,
                "name": class_data.name,
                # Add other class fields as needed
            },
            "financial_summary": {
                "total_collections": len(collections),
                "total_children": len(children),
                "total_expected": total_expected,
                "total_collected": total_collected,
                "total_outstanding": total_expected - total_collected,
                "total_withdrawn": total_withdrawn,
                "total_available_balance": total_collected - total_withdrawn,
            },
            "collections": collections_summary,
            "generated_date": date.today().isoformat(),
        }

        return class_report

    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(f"Error generating class financial report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate class financial report"
        )