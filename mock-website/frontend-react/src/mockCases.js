export const LIVE_SAMPLES = [
  // ── Cơ bản ────────────────────────────────────────────────────────────────
  {
    title: "basic — setTimeout với var",
    code: `// Lỗi cơ bản: for + var + setTimeout
for (var i = 0; i < 3; i++) {
  setTimeout(function() {
    console.log(i); // luôn in 3, 3, 3
  }, 100);
}`,
  },
  {
    title: "basic — async không có try/catch",
    code: `// Lỗi cơ bản: async function không bắt lỗi
async function loadUser(id) {
  const user = await db.findUser(id);
  return user;
}

loadUser(42);`,
  },
  {
    title: "basic — callback thiếu return",
    code: `// Lỗi cơ bản: thiếu return trong error path
function getUser(id, callback) {
  db.find(id, function(err, user) {
    if (err) callback(err); // thiếu return!
    callback(null, user);   // gọi callback lần 2
  });
}`,
  },
  {
    title: "basic — 3 await tuần tự độc lập",
    code: `// Lỗi cơ bản: 3 await không phụ thuộc nhau
async function getProfile(userId) {
  const user    = await db.users.findById(userId);
  const orders  = await db.orders.find(userId);
  const reviews = await db.reviews.find(userId);
  return { user, orders, reviews };
}`,
  },
  // ── Nâng cao ──────────────────────────────────────────────────────────────
  {
    title: "race_condition — db stock decrement",
    code: `// Race condition: concurrent stock decrement
async function purchaseItem(productId, userId) {
  const stock = await db.getStock(productId);
  if (stock <= 0) throw new Error("Out of stock");

  // Race window: another request reads stock = 1 here
  await db.setStock(productId, stock - 1);
  await db.createOrder({ productId, userId });
}`,
  },
  {
    title: "event_loop_blocking — readFileSync in loop",
    code: `// Event loop blocking: sync I/O inside async route
const fs = require('fs');

app.get('/config', async (req, res) => {
  const files = ['db.json', 'cache.json', 'auth.json'];
  const configs = {};

  for (const file of files) {
    // Blocks entire Node.js event loop!
    configs[file] = JSON.parse(fs.readFileSync(\`/config/\${file}\`));
  }

  res.json(configs);
});`,
  },
  {
    title: "zalgo — sync/async mixed callback",
    code: `// Zalgo: callback sometimes sync, sometimes async
function getUserData(userId, callback) {
  if (cache.has(userId)) {
    callback(null, cache.get(userId)); // sync path!
  } else {
    db.findUser(userId, function(err, user) {
      if (err) return callback(err);
      cache.set(userId, user);
      callback(null, user); // async path
    });
  }
}

// Caller assumes always async — broken when cache hits
getUserData(123, function(err, user) {
  console.log("got user:", user);
});
console.log("this may run AFTER the callback above!");`,
  },
  {
    title: "resource_exhaustion — Promise.all unlimited",
    code: `// Resource exhaustion: Promise.all with 1000 items
async function sendBulkEmails(userIds) {
  // Fires 1000 concurrent DB queries + HTTP calls
  // Crashes DB connection pool, exhausts memory
  const users = await Promise.all(
    userIds.map(id => db.users.findById(id))
  );

  await Promise.all(
    users.map(user => emailService.send(user.email, "Hello!"))
  );
}

// Called with userIds.length = 10000
await sendBulkEmails(allUserIds);`,
  },
  {
    title: "callback_hell — nested 4 levels deep",
    code: `// Callback hell: 4 levels of nesting
function processOrder(orderId, callback) {
  db.getOrder(orderId, function(err, order) {
    if (err) return callback(err);
    db.getUser(order.userId, function(err, user) {
      if (err) return callback(err);
      payment.charge(user.card, order.total, function(err, charge) {
        if (err) return callback(err);
        email.send(user.email, "Order confirmed", function(err) {
          if (err) return callback(err);
          callback(null, { order, charge });
        });
      });
    });
  });
}`,
  },
  {
    title: "missing_error_handler — stream pipe",
    code: `// Buffer leak: stream without error handler
const fs = require('fs');
const zlib = require('zlib');

app.get('/download/:file', (req, res) => {
  const readStream = fs.createReadStream(\`/data/\${req.params.file}\`);
  const gzip = zlib.createGzip();

  // No .on('error') handlers — stream error leaks memory
  // and crashes the process
  readStream.pipe(gzip).pipe(res);
});`,
  },
  {
    title: "singleton_race — lazy init shared state",
    code: `// Race condition: lazy singleton initialization
let dbConnection = null;

async function getConnection() {
  if (!dbConnection) {
    // Two concurrent requests both see null
    // Both call connect() → two connections created
    dbConnection = await db.connect();
  }
  return dbConnection;
}

app.get('/users', async (req, res) => {
  const conn = await getConnection();
  const users = await conn.query('SELECT * FROM users');
  res.json(users);
});`,
  },
  {
    title: "event_loop_ordering — nextTick vs setTimeout",
    code: `// Event loop ordering: wrong assumption about execution order
class DataLoader {
  constructor() {
    this.data = null;
    this.load();
  }

  load() {
    setTimeout(() => {
      this.data = { users: [1, 2, 3] };
    }, 0);
  }

  getData(callback) {
    // Assumes data is already loaded — wrong!
    process.nextTick(() => callback(this.data));
  }
}

const loader = new DataLoader();
loader.getData(data => {
  console.log(data.users); // TypeError: Cannot read 'users' of null
});`,
  },
];
