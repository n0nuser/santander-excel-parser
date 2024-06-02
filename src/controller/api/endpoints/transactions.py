"""Module with the endpoints for the transaction entity."""

import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, File, Path, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import UUID4
from sqlalchemy.orm import Session

from src.controller.api.endpoints.base import common_query_parameters
from src.controller.api.schemas.base import req_pagination
from src.controller.api.schemas.error_message import ErrorMessage
from src.controller.api.schemas.transactions.get_list_filters import req_transaction_filters
from src.controller.api.schemas.transactions.transactions import (
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
FiltersDeps = Annotated[
    tuple[list[Filter], OrderBy, OrderDirection],
    Depends(req_transaction_filters),
]
PaginationDeps = Annotated[tuple[int | None, int | None], Depends(req_pagination)]


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
    file: Annotated[UploadFile, File(description="File with transactions.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
) -> Response:
    """Endpoint to post the create transactions from a file."""
    logger.info("Entering...")
    start_time = time.time()
    # Check file content-type is XLS
    if file.content_type != "application/vnd.ms-excel":
        error_msg = (
            "Invalid file content-type. "  # noqa: ISC003
            + "Please use application/vnd.ms-excel content-type files."
        )
        raise HTTP400BadRequestError(error_msg)
    (
        account_number,
        succesful_transactions,
        already_exist_transactions,
    ) = await TransactionService.post_transactions_file(db_connection=db_connection, file=file)
    data = {
        "account_number": account_number,
        "succesful_transactions": succesful_transactions,
        "already_exist_transactions": already_exist_transactions,
    }
    http_request_info["location-id"] = account_number
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return JSONResponse(
        content=data,
        status_code=status.HTTP_201_CREATED,
        headers=http_request_info,
    )


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
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    filters: FiltersDeps,
    pagination: PaginationDeps,
    http_request_info: CommonDeps,
    request: Request,
    db_connection: Annotated[Session, Depends(get_db_session)],
) -> JSONResponse:
    """List of transactions."""
    logger.info("Entering...")
    start_time = time.time()
    logger.debug("Filters: %s", filters[0])

    limit = pagination[0]
    offset = pagination[1]
    transactions, count, from_date, to_date, statistics = TransactionService.get_transactions_list(
        db_connection=db_connection,
        account_number=account_number,
        limit=limit,
        offset=offset,
        statistics=filters[0],
        filters=filters[1],
        order_by=filters[2],
        order_direction=filters[3],
    )

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    path = request.scope.get("path", "")
    url_without_query_params = base_url + path
    if limit:
        if not offset:
            offset = 0
        api_pagination = Pagination().get_pagination(
            offset=offset, limit=limit, no_elements=count, url=url_without_query_params
        )
    else:
        api_pagination = None

    output = GetListTransactions(
        from_date=from_date,
        to_date=to_date,
        statistics=statistics,
        transactions=transactions,
        pagination=api_pagination,
    )
    response_data = jsonable_encoder(output.model_dump())
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK,
        headers=http_request_info,
    )


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
    start_time = time.time()
    output = TransactionService.get_transaction_id(
        db_connection=db_connection, transaction_id=transaction_id, account_number=account_number
    )

    response_data = jsonable_encoder(output.model_dump())
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return JSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK,
        headers=http_request_info,
    )


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
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    db_connection: Annotated[Session, Depends(get_db_session)],
    body: Annotated[DetailTransaction, Body(description="Transaction data.")],
) -> Response:
    """Endpoint to create a transaction."""
    logger.info("Entering...")
    start_time = time.time()
    transaction_id: UUID4 = TransactionService.post_transaction(
        db_connection=db_connection,
        data=body,
        account_number=account_number,
    )

    http_request_info["location-id"] = str(transaction_id)
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return Response(status_code=status.HTTP_201_CREATED, headers=http_request_info)


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
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    transaction_id: Annotated[UUID4, Path(description="Id of a specific transaction.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
    body: Annotated[DetailTransaction, Body(description="Transaction data.")],
) -> Response:
    """Update the information of the transaction with the matching Id."""
    logger.info("Entering...")
    start_time = time.time()
    TransactionService.put_transaction(
        db_connection=db_connection,
        transaction_id=transaction_id,
        account_number=account_number,
        data=body,
    )
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=http_request_info)


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
    account_number: Annotated[str, Path(description="Account Number", max_length=34)],
    transaction_id: Annotated[UUID4, Path(description="Id of a specific transaction.")],
    http_request_info: CommonDeps,
    db_connection: Annotated[Session, Depends(get_db_session)],
) -> Response:
    """Delete the information of the transaction with the matching Id."""
    logger.info("Entering...")
    start_time = time.time()
    TransactionService.delete_transaction(
        db_connection=db_connection, transaction_id=transaction_id, account_number=account_number
    )
    logger.info("Exiting (duration: %ss)...", time.time() - start_time)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=http_request_info)
