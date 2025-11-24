# Volunteer Authentication Pages Update

## Current Status
- volunteer_register.html: Basic template with only email/password fields, missing required fields
- volunteer_login.html: Template exists but has corrupted Firebase config causing rendering issues

## Plan
1. Update volunteer_register.html:
   - Add all required fields: name, email, phone, whatsapp_phone, vehicle_type, address, availability
   - Implement proper Firebase createUserWithEmailAndPassword
   - Add form validation and error handling
   - Send ID token to backend /register_volunteer route
   - Add success redirect to volunteer dashboard

2. Update volunteer_login.html:
   - Fix corrupted Firebase config
   - Implement proper Firebase signInWithEmailAndPassword
   - Add form validation and error handling
   - Send ID token to backend /login_volunteer route
   - Add success redirect to volunteer dashboard

3. Ensure consistent styling with existing pages
4. Test Firebase integration and backend communication

## Dependent Files
- Templates/volunteers/volunteer_register.html
- Templates/volunteers/volunteer_login.html
- routes/auth_routes.py (routes already exist)

## Followup Steps
- Test registration flow
- Test login flow
- Verify redirects work
- Check form validation
