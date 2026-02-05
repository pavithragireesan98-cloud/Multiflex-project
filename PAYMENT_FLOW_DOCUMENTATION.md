# MULTIFLEX Accept/Reject Payment Flow - Complete Checklist

## ROUTES IMPLEMENTED

### ✅ Accept Payment Route
**Route:** `/user_accept_payment/<int:req_id>`
**File:** `c:\wamp64\www\multiflex\user.py` (Lines 95-116)
**Function:**
- Updates `request_master` table: `user_decision='accepted'`
- Fetches amount from `proposals` table
- Redirects to `/pay?req_id=X&amount=Y`

### ✅ Reject Assigned Route  
**Route:** `/user_reject_assigned/<int:req_id>`
**File:** `c:\wamp64\www\multiflex\user.py` (Lines 143-153)
**Function:**
- Updates `request_master` table: `user_decision='rejected'`
- Updates `proposals` table: `status='rejected'`
- Returns to My Requests page

### ✅ Payment Page Route
**Route:** `/pay`
**File:** `c:\wamp64\www\multiflex\user.py` (Lines 266-295)
**Function:**
- Accepts GET params: `?req_id=X&amount=Y`
- Creates Razorpay order
- Renders beautiful payment page

### ✅ Payment Success Route
**Route:** `/payment_success/<int:req_id>`
**File:** `c:\wamp64\www\multiflex\user.py` (Lines 298-307)
**Function:**
- Updates `request_master`: `user_decision='paid', status='paid'`
- Updates `proposals`: `status='paid'`
- Redirects to My Requests page

## TEMPLATE UPDATES

### ✅ user_my_request_worker.html
**File:** `c:\wamp64\www\multiflex\templates\user_my_request_worker.html`
**Changes:**
- Line 87: Accept button links to `/user_accept_payment/{{ row['request_id'] }}`
- Line 88: Reject button links to `/user_reject_assigned/{{ row['request_id'] }}`
- Conditions:
  - If `worker_status == "assigned"` AND `pay_amount > 0`: Show Accept | Reject buttons
  - If `user_decision == "paid"`: Show ✔ Paid
  - If `user_decision == "accepted"`: Show ✔ Accepted
  - If `user_decision == "rejected"`: Show ❌ Rejected
  - Else: Show Pending

### ✅ payment.html
**File:** `c:\wamp64\www\multiflex\templates\payment.html`
**Features:**
- Beautiful gradient background
- Large amount display (₹)
- Payment details box
- "💳 Pay Now" and "Cancel" buttons
- Security badge
- Razorpay integration

## DATABASE FLOW

### Request Workflow:
```
User requests worker (pending)
  ↓
Worker accepts & sets work date/time (assigned + proposal created)
  ↓
User sees "✔ Accept | ❌ Reject" buttons
  ↓
User clicks Accept
  ↓
Updates user_decision='accepted'
Redirects to /pay?req_id=X&amount=Y
  ↓
Beautiful payment page loads
  ↓
User clicks "💳 Pay Now"
  ↓
Razorpay checkout opens
  ↓
Payment successful
  ↓
Redirects to /payment_success/{req_id}
  ↓
Updates both tables with 'paid' status
  ↓
Returns to My Requests - shows ✔ Paid
```

### Reject Workflow:
```
User sees "✔ Accept | ❌ Reject" buttons
  ↓
User clicks Reject
  ↓
/user_reject_assigned/{req_id} executes
  ↓
Updates request_master: user_decision='rejected'
Updates proposals: status='rejected'
  ↓
Returns to My Requests - shows ❌ Rejected
```

## TESTING CHECKLIST

### Step 1: Verify Data
1. Open phpMyAdmin
2. Check `request_master` table
   - Find row with status='assigned' and user_decision=NULL/empty
   - Note the `request_id` and verify `worker_status='assigned'`
3. Check `proposals` table
   - Verify the same request has a proposal entry with an amount
   - Example: `amount=500`

### Step 2: Test Accept Button
1. Go to `/user_my_request_worker`
2. Find row with status='assigned'
3. Click "✔ Accept" button
4. Expected: Redirects to payment page with amount displayed
5. Verify in phpMyAdmin: `request_master.user_decision` should now be 'accepted'

### Step 3: Test Payment Page
1. On payment page, verify:
   - Amount displays correctly (e.g., ₹500)
   - Service type shown
   - Currency: INR
   - Payment Method: Razorpay
2. Click "💳 Pay Now"
3. Razorpay modal should appear

### Step 4: Test Payment Success
1. Complete payment in Razorpay (use test card if available)
2. Expected: Redirects to `/payment_success/{req_id}`
3. Shows success message
4. Verify in phpMyAdmin:
   - `request_master`: `user_decision='paid'`, `status='paid'`
   - `proposals`: `status='paid'`
5. Go back to My Requests - row should show ✔ Paid

### Step 5: Test Reject Button
1. Go to `/user_my_request_worker`
2. Find row with status='assigned' (create a new request if needed)
3. Click "❌ Reject" button
4. Expected: Immediately returns to My Requests
5. Row should show ❌ Rejected
6. Verify in phpMyAdmin:
   - `request_master.user_decision='rejected'`
   - `proposals.status='rejected'`

## TROUBLESHOOTING

### Issue: Accept/Reject buttons not appearing
**Cause:** `worker_status != 'assigned'` OR `pay_amount <= 0`
**Solution:** 
1. Check request is assigned (worker_status='assigned')
2. Check proposal exists with amount > 0
3. View page source - should show HTML `<a>` tags

### Issue: Clicking Accept gives 404 error
**Cause:** Route not found
**Solution:**
1. Verify route in user.py exists (line 95)
2. Check URL format: `/user_accept_payment/1` (not `/user/accept_payment/1`)
3. Restart Flask server

### Issue: Payment page blank/broken
**Cause:** Razorpay keys invalid or `request_id` not passed
**Solution:**
1. Check GET params: URL should be `/pay?req_id=1&amount=500`
2. Verify Razorpay test keys are correct
3. Check browser console for JavaScript errors

### Issue: Payment success not updating database
**Cause:** Razorpay callback not executing
**Solution:**
1. Check if payment actually completed
2. Verify `/payment_success/<id>` route exists
3. Check MySQL error logs

## FILES MODIFIED

✅ `user.py` - Routes for accept, reject, payment
✅ `templates/user_my_request_worker.html` - Accept/Reject buttons
✅ `templates/payment.html` - Payment page design

## IMPORTANT NOTES

1. Routes are registered in the `user` blueprint without URL prefix
2. All routes require `session['user_id']` to be set (login required)
3. Request IDs must be integers (Flask validates with `<int:req_id>`)
4. Payment amounts come from `proposals` table, not hardcoded
5. Both `request_master` and `proposals` tables updated on payment success

