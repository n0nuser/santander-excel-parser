"""Module with the endpoints for the transaction entity."""

import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, File, Path, Query, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import UUID4
from sqlalchemy.orm import Session

from src.controller.api.endpoints.base import common_query_parameters
from src.controller.api.schemas.error_message import ErrorMessage
from src.controller.api.schemas.transactions import (
    DetailTransaction,
    FullDetailTransaction,
    GetListTransactions,
    OrderBy,
    OrderDirection,
)
from src.controller.errors.exceptions import HTTP400BadRequestError
from src.controller.utils.pagination import Pagination
from src.repository.crud.base import Filter
from src.repository.session import get_db_session
from src.service.transaction.service import TransactionService

logger = logging.getLogger(__name__)

router = APIRouter()

CommonDeps = Annotated[dict[str, Any], Depends(common_query_parameters)]


@router.post(
    "/v1/transactions/",
    responses={
        201: {"description": "Created."},
        400: {"model": ErrorMessage, "description": "Bad Request."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="Uploads .xls file with transactions from Santander Bank.",
    response_class=Response,
)
async def post_transactions_file(
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
    file: Annotated[UploadFile, File(description="File with transactions.")],
) -> Response:
    """Endpoint to post the create transactions from a file."""
    logger.info("Entering...")
    # Check file content-type is XLS
    if file.content_type != "application/vnd.ms-excel":
        error_msg = (
            "Invalid file content-type. "  # noqa: ISC003
            + "Please use application/vnd.ms-excel content-type files."
        )
        raise HTTP400BadRequestError(error_msg)
    account_id = await TransactionService.post_transactions_file(
        db_connection=db_connection, file=file
    )
    http_request_info["location_id"] = account_id
    logger.info("Exiting...")
    return Response(status_code=201, headers=http_request_info)


@router.get(
    "/v1/accounts/{account_number}/transactions",
    responses={
        200: {"model": GetListTransactions, "description": "OK."},
        400: {"model": ErrorMessage, "description": "Bad Request."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="List of transactions.",
    response_model_by_alias=True,
    response_model=GetListTransactions,
)
async def get_transactions(
    http_request_info: CommonDeps,
    request: Request,
    db_connection: Annotated[Session, Depends(get_db_session)],
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    concept: Annotated[
        str | None,
        Query(
            description="Concept of the transaction.",
            example="Compra Apple.com/bill, Itunes.com, Tarjeta 543719440150905 , Comision 0,00",
        ),
    ] = None,
    amount: Annotated[
        int | None,
        Query(description="Amount of the transaction.", example="0.00"),
    ] = None,
    amount_start_range: Annotated[
        int | None,
        Query(description="Amount start range of the transaction.", example="0.00"),
    ] = None,
    amount_end_range: Annotated[
        int | None,
        Query(description="Amount end range of the transaction.", example="0.00"),
    ] = None,
    operation_date: Annotated[
        str | None,
        Query(description="Operation date of the transaction.", example="2021-07-27"),
    ] = None,
    operation_start_range_date: Annotated[
        str | None,
        Query(description="Operation start range date of the transaction.", example="2021-07-27"),
    ] = None,
    operation_end_range_date: Annotated[
        str | None,
        Query(description="Operation end range date of the transaction.", example="2021-07-27"),
    ] = None,
    order_by: Annotated[
        OrderBy,
        Query(description="Order by field. Default is operation date."),
    ] = OrderBy.operation_original_date,
    order_direction: Annotated[
        OrderDirection,
        Query(description="Order direction. Default is descending."),
    ] = OrderDirection.DESCENDING,
    limit: Annotated[
        int,
        Query(
            description="Number of records returned per page."  # noqa: ISC003
            + " If specified on entry, this will be the value of the query,"
            + " otherwise it will be the value value set by default.",
            ge=1,
            le=100,
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            description="Record number from which you want to receive"  # noqa: ISC003
            + " the number of records indicated in the limit."
            + " If it is indicated at the entry, it will be the value of the query."
            + " If it is not indicated at the input, as the query is on the first page,"
            + " its value will be 0.",
            ge=0,
            le=100,
        ),
    ] = 0,
) -> JSONResponse:
    """List of transactions."""
    logger.info("Entering...")
    if amount and (amount_start_range or amount_end_range):
        error_msg = "You can't use amount and amount range at the same time."
        raise HTTP400BadRequestError(error_msg)
    if (amount_start_range and not amount_end_range) or (
        not amount_start_range and amount_end_range
    ):
        error_msg = "You must use both amount range fields."
        raise HTTP400BadRequestError(error_msg)

    if operation_date and (operation_start_range_date or operation_end_range_date):
        error_msg = "You can't use operation date and operation date range at the same time."
        raise HTTP400BadRequestError(error_msg)
    if (operation_start_range_date and not operation_end_range_date) or (
        not operation_start_range_date and operation_end_range_date
    ):
        error_msg = "You must use both operation date range fields."
        raise HTTP400BadRequestError(error_msg)

    filters: list[Filter] = []
    if concept:
        filters.append(Filter(field="concept", operator="contains", value=concept))
    if amount:
        filters.append(Filter(field="amount", operator="eq", value=amount))
    if amount_start_range:
        filters.append(Filter(field="amount", operator="gte", value=amount_start_range))
    if amount_end_range:
        filters.append(Filter(field="amount", operator="lte", value=amount_end_range))
    if operation_date:
        if (
            operation_date
            and not datetime.strptime(operation_date, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        ):
            error_msg = "Invalid operation date format. Please use YYYY-MM-DD."
            raise HTTP400BadRequestError(error_msg)
        filters.append(Filter(field="operation_original_date", operator="eq", value=operation_date))
    if operation_start_range_date:
        if (
            operation_date
            and not datetime.strptime(operation_date, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        ):
            error_msg = "Invalid operation date format. Please use YYYY-MM-DD."
            raise HTTP400BadRequestError(error_msg)
        filters.append(
            Filter(
                field="operation_original_date", operator="gte", value=operation_start_range_date
            )
        )
    if operation_end_range_date:
        if (
            operation_date
            and not datetime.strptime(operation_date, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        ):
            error_msg = "Invalid operation date format. Please use YYYY-MM-DD."
            raise HTTP400BadRequestError(error_msg)
        filters.append(
            Filter(field="operation_original_date", operator="lte", value=operation_end_range_date)
        )
    logger.debug("Filters: %s", filters)

    transactions, count = TransactionService.get_transactions_list(
        db_connection=db_connection,
        account_number=account_number,
        limit=limit,
        offset=offset,
        filters=filters,
        order_by=order_by,
        order_direction=order_direction,
    )

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    path = request.scope.get("path", "")
    url_without_query_params = base_url + path
    pagination = Pagination().get_pagination(offset, limit, count, url_without_query_params)

    output = GetListTransactions(data=transactions, pagination=pagination)
    response_data = jsonable_encoder(output.model_dump())
    logger.info("Exiting...")
    return JSONResponse(content=response_data, status_code=200, headers=http_request_info)


@router.get(
    "/v1/accounts/{account_number}/transactions/{transaction_id}",
    responses={
        200: {"model": FullDetailTransaction, "description": "OK."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        404: {"model": ErrorMessage, "description": "Not Found."},
        422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
        423: {"model": ErrorMessage, "description": "Locked."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        501: {"model": ErrorMessage, "description": "Not Implemented."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="Transaction information.",
    response_model_by_alias=True,
    response_model=FullDetailTransaction,
)
async def get_transaction_id(
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    transaction_id: Annotated[UUID4, Path(description="Id of a specific transaction.")],
) -> JSONResponse:
    """Retrieve the information of the transaction with the matching code."""
    logger.info("Entering...")
    output = TransactionService.get_transaction_id(
        db_connection=db_connection, transaction_id=transaction_id, account_number=account_number
    )

    response_data = jsonable_encoder(output.model_dump())
    logger.info("Exiting...")
    return JSONResponse(content=response_data, status_code=200, headers=http_request_info)


@router.post(
    "/v1/accounts/{account_number}/transactions",
    responses={
        200: {"description": "OK."},
        400: {"model": ErrorMessage, "description": "Bad Request."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="Creates a new transaction.",
    response_class=Response,
)
async def post_transaction(
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
    body: Annotated[DetailTransaction, Body(description="Transaction data.")],
) -> Response:
    """Endpoint to create a transaction."""
    logger.info("Entering...")
    transaction_id: UUID4 = TransactionService.post_transaction(
        db_connection=db_connection,
        data=body,
    )

    http_request_info["location_id"] = str(transaction_id)
    logger.info("Exiting...")
    return Response(status_code=200, headers=http_request_info)


@router.put(
    "/v1/accounts/{account_number}/transactions/{transaction_id}",
    responses={
        200: {"description": "OK."},
        400: {"model": ErrorMessage, "description": "Bad Request."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        422: {"model": ErrorMessage, "description": "Unprocessable Entity."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="Update specific transaction.",
    response_model=None,
)
async def put_transaction(
    transaction_id: Annotated[UUID4, Path(description="Id of a specific transaction.")],
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
    body: Annotated[DetailTransaction, Body(description="Transaction data.")],
) -> Response:
    """Update the information of the transaction with the matching Id."""
    logger.info("Entering...")
    TransactionService.put_transaction(
        db_connection=db_connection,
        transaction_id=transaction_id,
        account_number=account_number,
        data=body,
    )
    logger.info("Exiting...")
    return Response(status_code=200, headers=http_request_info)


@router.delete(
    "/v1/accounts/{account_number}/transactions/{transaction_id}",
    responses={
        204: {"description": "No Content."},
        400: {"model": ErrorMessage, "description": "Bad Request."},
        401: {"model": ErrorMessage, "description": "Unauthorized."},
        403: {"model": ErrorMessage, "description": "Forbidden."},
        404: {"model": ErrorMessage, "description": "Not Found."},
        500: {"model": ErrorMessage, "description": "Internal Server Error."},
        502: {"model": ErrorMessage, "description": "Bad Gateway."},
        503: {"model": ErrorMessage, "description": "Service Unavailable."},
        504: {"model": ErrorMessage, "description": "Gateway Timeout."},
    },
    tags=["Transactions"],
    summary="Delete specific transaction.",
    response_model=None,
)
async def delete_transaction_id(
    transaction_id: Annotated[UUID4, Path(description="Id of a specific transaction.")],
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
) -> Response:
    """Delete the information of the transaction with the matching Id."""
    logger.info("Entering...")
    TransactionService.delete_transaction(
        db_connection=db_connection, transaction_id=transaction_id, account_number=account_number
    )
    logger.info("Exiting...")
    return Response(status_code=204, headers=http_request_info)
