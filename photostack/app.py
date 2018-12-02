import json
import os
import uuid
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key, Attr

DUMMY_USER_ID = "foobar"
TABLE_NAME = os.environ.get("TABLE_NAME", "dummy_table")
GSI_NAME = os.environ.get("GSI_NAME", "dummy_gsi")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def respond(err, resp=None):
    return {
        "statusCode": 400 if err else 200,
        "body": repr(err) if err else json.dumps(resp),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
    }


def create_photo(table, user_id, **data):
    photo_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    item = dict(id=photo_id, uid=user_id, crtTs=now, updTs=now)
    other_attrs = {
        attr: data.pop(attr, None) for attr in ("img", "imgXs", "title", "desc")
    }
    item.update(**{k: v for k, v in other_attrs.items() if v is not None})
    table.put_item(Item=item, ConditionExpression=Attr("id").not_exists())
    return item


def list_photos(table, index_name, user_id):
    now = datetime.utcnow().isoformat()
    resp = table.query(
        IndexName=index_name,
        ProjectionExpression="id,crtTs,updTs,title,img,imgXs",
        KeyConditionExpression=Key("uid").eq(user_id) & Key("crtTs").lte(now),
    )
    return {"items": resp["Items"]}


OPERATIONS = {
    "POST": lambda **kw: create_photo(table, kw.pop("user_id"), **kw),
    "GET": lambda **kw: list_photos(table, GSI_NAME, kw.pop("user_id")),
}


def handler(event, context):
    method = event["httpMethod"]
    if method not in OPERATIONS:
        return respond(ValueError(f'Unsupported http method "{method}"'))

    payload = json.loads(event.get("body") or "{}")
    user_id = context.identity.cognito_identity_id or DUMMY_USER_ID
    resp = OPERATIONS[method](user_id=user_id, **payload)
    return respond(None, resp=resp)
