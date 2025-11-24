# TODO for Creating Food Donors Database

## Steps to Complete
- [x] Add `food_donors` table in `database/models.py` with columns: organization_name, food_type, quantity, ready_for_pickup_time, pickup_location, category (default NULL), cuisine_type (default NULL), spice_level (default NULL)
- [x] Modify `routes/donor_routes.py` to insert donation data into `food_donors` table instead of `food_requests`, updating field names accordingly
- [x] Test the donation submission manually to ensure data is stored correctly in the new table
