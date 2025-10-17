The status transition that is missing between accepted and picked_up is in_transit.

Based on the status transition logic defined in app/services/order_service.py, the valid transitions are:

PENDING 
→
→ ACCEPTED or CANCELLED
ACCEPTED 
→
→ IN_TRANSIT or CANCELLED
IN_TRANSIT 
→
→ PICKED_UP or CANCELLED
PICKED_UP 
→
→ DELIVERED or CANCELLED
DELIVERED 
→
→ COMPLETED


-25.405697690400196, 28.27002167609345