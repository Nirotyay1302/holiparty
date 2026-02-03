// MongoDB Playground for Holi Party Website Moderation
// Use this to query and moderate bookings data

// Select the database
use('holi_party');

// 1. View all bookings
db.bookings.find().limit(10);

// 2. Count total bookings
db.bookings.countDocuments();

// 3. Find bookings with pending payment
db.bookings.find({ payment_status: 'Pending' });

// 4. Find bookings with paid status
db.bookings.find({ payment_status: 'Paid' });

// 5. Find bookings with entry status 'Not Used'
db.bookings.find({ entry_status: 'Not Used' });

// 6. Update a booking's entry status to 'Used' (replace with actual ticket_id)
db.bookings.updateOne(
  { ticket_id: 'YOUR_TICKET_ID_HERE' },
  { $set: { entry_status: 'Used' } }
);

// 7. Update payment status to 'Paid' (for manual approval)
db.bookings.updateOne(
  { order_id: 'YOUR_ORDER_ID_HERE' },
  { $set: { payment_status: 'Paid' } }
);

// 8. Delete a booking (use with caution)
db.bookings.deleteOne({ ticket_id: 'YOUR_TICKET_ID_HERE' });

// 9. Aggregate: Count bookings by payment status
db.bookings.aggregate([
  { $group: { _id: '$payment_status', count: { $sum: 1 } } }
]);

// 10. Aggregate: Total revenue from paid bookings
db.bookings.aggregate([
  { $match: { payment_status: 'Paid' } },
  { $group: { _id: null, total_passes: { $sum: '$passes' }, total_revenue: { $sum: { $multiply: ['$passes', 200] } } } }
]);

// 11. Find recent bookings (last 7 days)
db.bookings.find({
  created_at: { $gte: new Date(Date.now() - 7*24*60*60*1000) }
}).sort({ created_at: -1 });

// Note: Add created_at field to bookings if not present
// To add timestamps, modify the Booking model in models.py to include timestamps