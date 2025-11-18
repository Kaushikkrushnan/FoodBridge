# TODO: Implement NGO Accept Donations and Update Dashboards

## Completed Features:
- [x] Add /accept_food_request route in ngo_routes.py: accepts ngo_id, request_id, sets ngo_id, status='assigned', assigns nearest volunteer.
- [x] Update donor_dashboard in dashboard_routes.py: query distinct NGOs with accepted donations, return as accepted_ngos.
- [x] Update Donor_dashboard.html: change section to "Accepted Food Donors", template to show NGO cards.
- [x] Update NGO_dashboard.html JS: replace simulation with real API call to accept request.

## Followup steps:
- [x] Test NGO accept functionality
- [x] Test donor dashboard shows accepted NGOs
- [x] Verify volunteer assignment
