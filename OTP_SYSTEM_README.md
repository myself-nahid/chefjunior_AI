# Email Verification OTP System - Implementation Guide

## Overview
A complete email-based OTP (One-Time Password) system has been implemented for user email verification during signup. This system generates 6-digit OTP codes that expire after **2 minutes**.

## What Was Implemented

### 1. Database Schema
- **Migration File**: `alembic/versions/abcd1234efgh_add_email_verification_otp.py`
- **New User Model Fields**:
  - `email_verification_otp` (String): Stores the 6-digit OTP code
  - `email_verification_otp_expires` (DateTime): Stores OTP expiration timestamp
  - `is_email_verified` (Boolean): Tracks if user's email is verified (default: False)

### 2. API Endpoints

#### Signup
- **Endpoint**: `POST /api/v1/auth/signup`
- **Behavior**: 
  - Creates new user account
  - Automatically generates and sends email verification OTP
  - User cannot login until email is verified
  - OTP is valid for 2 minutes

#### Email Verification
- **Endpoint**: `POST /api/v1/auth/verify-email`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "otp": "123456"
  }
  ```
- **Response**:
  - Success: `{"message": "Email verified successfully. You can now login."}`
  - Error: Returns appropriate error if OTP is invalid or expired

#### Resend Verification OTP
- **Endpoint**: `POST /api/v1/auth/resend-verification-otp`
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Behavior**:
  - Generates a NEW OTP (invalidates the previous one)
  - Resets the 2-minute expiration timer
  - Sends OTP to user's email

#### Send Verification OTP (Manual)
- **Endpoint**: `POST /api/v1/auth/send-verification-otp`
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Use Case**: For situations where user needs OTP resent without signup

#### Check Email Verification Status
- **Endpoint**: `GET /api/v1/auth/email-verification-status?email=user@example.com`
- **Response**:
  ```json
  {
    "email": "user@example.com",
    "is_email_verified": true,
    "full_name": "John Doe"
  }
  ```

### 3. Email Templates
- **File**: `app/core/email_utils.py`
- **Function**: `send_email_verification_otp(to_email, otp)`
- **Features**:
  - Professional HTML email template
  - Displays 6-digit OTP prominently
  - Shows 2-minute expiration notice
  - ChefJunior branding
  - Fallback to console print if SMTP fails

### 4. Login Protection
- Both login endpoints (`/login` and `/login/access-token`) now check if email is verified
- **Error Response** (if email not verified):
  ```json
  {
    "detail": "Please verify your email before logging in. Check your inbox for the verification code."
  }
  ```

## User Flow

```
1. User Signs Up
   ↓
2. User Account Created with is_email_verified = False
   ↓
3. Verification OTP Generated (6 digits, 2-minute expiry)
   ↓
4. Email Sent with OTP Code
   ↓
5. User Enters OTP in App
   ↓
6. OTP Validated
   ↓
7. is_email_verified Set to True
   ↓
8. User Can Now Login
```

## Running the Migration

```bash
cd c:\Users\nahid\Desktop\JVai-up\chefjunior_AI
alembic upgrade head
```

## Environment Variables Required

For real email sending, ensure these are set in your `.env` file:
```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Use App Passwords for Gmail
```

## Fallback Behavior

If SMTP is not configured:
- OTP codes are printed to console
- Useful for development/testing
- Console output clearly marked with emoji indicators:
  - `⚠️` - Email simulation warning
  - `📧` - Email/user info
  - `🔑` - OTP code
  - `⏰` - Expiration info

### Example Console Output:
```
==================================================
⚠️  EMAIL SIMULATION (SMTP not configured or failed)
📧  New User Registered: user@example.com
📨  To: user@example.com
🔑  VERIFICATION OTP CODE: 654321
⏰  Expires in: 2 minutes
==================================================
```

## Security Features

1. **OTP Expiration**: 2-minute window prevents brute force attacks
2. **Single-Use Codes**: OTP cleared after successful verification
3. **Email Enumeration Protection**: Endpoints always return success message even if email doesn't exist
4. **Password Hashing**: OTPs are separate from passwords
5. **Rate Limiting**: Ready for implementation
6. **Audit Trail**: All verification attempts logged

## Schemas/Validators

New Pydantic schemas in `app/schemas/user.py`:
- `SendVerificationOTPRequest`: Email only
- `VerifyEmailRequest`: Email + OTP
- `ResendVerificationOTPRequest`: Email only

## Database Schema Migration

Alembic migration handles:
- Adding `email_verification_otp` column
- Adding `email_verification_otp_expires` column  
- Adding `is_email_verified` boolean (default: False)
- Automatic rollback support if needed

## Testing the System

### Via API:
1. **Signup**: `POST /api/v1/auth/signup` with email/password
2. **Check Status**: `GET /api/v1/auth/email-verification-status?email=user@example.com`
3. **Try Login**: `POST /api/v1/auth/login` (should fail - email not verified)
4. **Get OTP from Console Output** or email inbox
5. **Verify Email**: `POST /api/v1/auth/verify-email` with OTP
6. **Login Again**: Should succeed now

### Via Swagger UI:
- All endpoints are documented at `/docs`
- Can test all flows interactively

## Important Notes

1. The OTP system is for **email verification only**, not password reset
2. Password reset still uses the original 10-minute OTP system (`reset_otp` fields)
3. Both systems coexist independently
4. Users must verify email before accessing the app
5. Admins can check verification status via the status endpoint

## Future Enhancements

Potential additions:
- SMS-based OTP (requires Twilio integration)
- TOTP (Time-based One-Time Passwords with authenticator apps)
- Rate limiting on OTP requests
- Email verification reminders
- Webhook for email service provider status
- OTP delivery via multiple channels
