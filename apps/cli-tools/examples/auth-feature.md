# User Authentication Feature

## Overview
Implement a complete user authentication system with email/password and OAuth support.

## Requirements

### Core Authentication
- User registration with email and password
- Email verification flow
- Password reset functionality
- Login with email/password
- Session management with JWT tokens
- Refresh token rotation

### OAuth Integration
- Google OAuth 2.0 integration
- GitHub OAuth integration
- OAuth account linking

### Security
- Password hashing with bcrypt
- Rate limiting on authentication endpoints
- CSRF protection
- Secure cookie handling
- Account lockout after failed attempts

### User Management
- User profile management
- Account deletion
- Email change flow
- Password change flow

## Acceptance Criteria
- [ ] Users can register with email/password
- [ ] Users can login with email/password
- [ ] Users can login with Google OAuth
- [ ] Users can login with GitHub OAuth
- [ ] Email verification works
- [ ] Password reset works
- [ ] JWT tokens are properly issued and validated
- [ ] Rate limiting prevents abuse
- [ ] Security best practices are followed

## Technical Details
- Use JWT for session tokens
- Store refresh tokens in database
- Use bcrypt for password hashing (cost factor 12)
- Implement rate limiting: 5 attempts per 15 minutes
- OAuth redirect URLs must be whitelisted

