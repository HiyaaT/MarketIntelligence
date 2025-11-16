from flask_restful import Resource, reqparse
from flask import jsonify, request, make_response
from flask_security import hash_password, utils, auth_token_required, current_user
from applications.user_datastore import user_datastore
from applications.database import db
from applications.models import User, Watchlist 
from sqlalchemy.sql import exists
from sqlalchemy.exc import IntegrityError
import uuid
import pandas as pd
import yfinance as yf