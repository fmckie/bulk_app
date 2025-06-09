"""
Authentication helper functions for Supabase Auth
"""
from functools import wraps
from flask import request, jsonify, session
from database.connection import supabase
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session token first (web app)
        if 'access_token' in session:
            try:
                # Verify token with Supabase
                user = supabase.auth.get_user(session['access_token'])
                if user:
                    request.current_user = user
                    return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Session token validation failed: {str(e)}")
                session.pop('access_token', None)
        
        # Check for Authorization header (API)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.replace('Bearer ', '')
                user = supabase.auth.get_user(token)
                if user:
                    request.current_user = user
                    return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Bearer token validation failed: {str(e)}")
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function


def get_current_user():
    """Get the current authenticated user"""
    if hasattr(request, 'current_user'):
        return request.current_user
    
    # Try session
    if 'access_token' in session:
        try:
            user = supabase.auth.get_user(session['access_token'])
            return user
        except:
            pass
    
    # Try Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.replace('Bearer ', '')
            user = supabase.auth.get_user(token)
            return user
        except:
            pass
    
    return None


def get_current_user_id():
    """Get the current user's ID"""
    user = get_current_user()
    if user and hasattr(user, 'user') and hasattr(user.user, 'id'):
        return user.user.id
    return None


class AuthService:
    """Authentication service for Supabase"""
    
    @staticmethod
    def sign_up(email, password, profile_data=None):
        """Sign up a new user"""
        try:
            # Create user
            response = supabase.auth.sign_up({
                'email': email,
                'password': password
            })
            
            if response.user and profile_data:
                # Create profile
                from database.connection import ProfileDB
                profile_data['email'] = email
                ProfileDB.create_or_update_profile(response.user.id, profile_data)
            
            return {
                'success': True,
                'user': response.user,
                'session': response.session
            }
        except Exception as e:
            logger.error(f"Sign up failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sign_in(email, password):
        """Sign in a user"""
        try:
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            return {
                'success': True,
                'user': response.user,
                'session': response.session
            }
        except Exception as e:
            logger.error(f"Sign in failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sign_out(token=None):
        """Sign out the current user"""
        try:
            if token:
                supabase.auth.sign_out(token)
            else:
                supabase.auth.sign_out()
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Sign out failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_oauth_url(provider):
        """Get OAuth sign in URL"""
        try:
            response = supabase.auth.sign_in_with_oauth({
                'provider': provider,
                'options': {
                    'redirect_to': f"{request.host_url}auth/callback"
                }
            })
            
            return {
                'success': True,
                'url': response.url
            }
        except Exception as e:
            logger.error(f"OAuth URL generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def refresh_session(refresh_token):
        """Refresh an auth session"""
        try:
            response = supabase.auth.refresh_session(refresh_token)
            
            return {
                'success': True,
                'session': response.session
            }
        except Exception as e:
            logger.error(f"Session refresh failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }