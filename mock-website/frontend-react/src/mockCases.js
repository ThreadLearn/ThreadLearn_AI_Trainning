export const MOCK_CASES = [
  {
    title: "closure_loop_var — for+var+setTimeout",
    code: `// Bug: for-loop với var + setTimeout callback
// Source: classic JS closure pitfall

function scheduleNotifications(users) {
  for (var i = 0; i < users.length; i++) {
    setTimeout(function() {
      console.log("Sending to user:", users[i]);
      sendEmail(users[i].email, "Hello!");
    }, i * 100);
  }
}

// users[i] lúc callback chạy: i = users.length
// Tất cả callback nhận cùng giá trị i cuối cùng`,
    response: {
      issues: [
        {
          severity: "high",
          pattern_id: "closure_loop_var",
          line_range: "5-9",
          description: "Biến var i được share qua tất cả setTimeout callbacks. Khi callback chạy, i đã = users.length.",
          fix: "Thay var → let:\nfor (let i = 0; i < users.length; i++) { ... }",
        },
      ],
      docs_used: [
        { id: "d001", title: "Closure Loop Variable", category: "race-condition" },
        { id: "d012", title: "var vs let Scope", category: "fundamentals" },
        { id: "d018", title: "Event Loop Timing", category: "async" },
      ],
      explanation: "Đây là <strong>Closure Loop Variable</strong> — bug JS cổ điển. Khi dùng <strong>var</strong>, biến i tồn tại trong scope hàm, không phải từng iteration. Tất cả callbacks giữ reference đến cùng biến i. Khi event loop chạy callbacks, i đã = users.length.\n\nFix: dùng <strong>let</strong> — tạo binding riêng mỗi iteration.",
    },
  },
  {
    title: "double_callback — mysql query pattern",
    code: `// Bug: double callback — mysql pattern
// Source: github.com/mysqljs/mysql/issues/1260

function queryUser(userId, callback) {
  connection.connect(function(err) {
    if (err) callback(err);  // thiếu return!

    connection.query(
      "SELECT * FROM users WHERE id = ?",
      [userId],
      function(err, results) {
        callback(err, results);  // callback gọi lần 2!
      }
    );
  });
}`,
    response: {
      issues: [
        {
          severity: "high",
          pattern_id: "double_callback",
          line_range: "5-6",
          description: "Thiếu return trước callback(err). Khi lỗi, callback gọi lần 1, nhưng hàm tiếp tục chạy.",
          fix: "Thêm return:\nif (err) return callback(err);",
        },
        {
          severity: "medium",
          pattern_id: "double_callback",
          line_range: "8-13",
          description: "Query vẫn chạy dù callback đã được gọi với lỗi.",
          fix: "Cấu trúc lại với early return ở mọi error path.",
        },
      ],
      docs_used: [
        { id: "d005", title: "Double Callback Pattern", category: "callback" },
        { id: "d019", title: "Error-First Callbacks", category: "callback" },
        { id: "d021", title: "Early Return Pattern", category: "patterns" },
      ],
      explanation: "Pattern <strong>Double Callback</strong> xảy ra khi thiếu <strong>return</strong> trong error path. Node.js convention: callback chỉ gọi <em>đúng một lần</em>. Khi callback bị gọi 2 lần, app có thể crash hoặc corrupt state.\n\nFix: <strong>return callback(err)</strong> để dừng execution ngay.",
    },
  },
  {
    title: "unhandled_rejection — async route no catch",
    code: `// Bug: async route handler không có try/catch
// Source: github.com/expressjs/express/issues/2700

const express = require('express');
const app = express();

app.get('/user/:id', async function(req, res) {
  const user = await db.findUser(req.params.id);
  res.json(user);
});

app.get('/orders/:userId', async function(req, res) {
  const orders = await db.getOrders(req.params.userId);
  const totals = await paymentService.getTotals(orders);
  res.json({ orders, totals });
});`,
    response: {
      issues: [
        {
          severity: "high",
          pattern_id: "unhandled_rejection",
          line_range: "7-9",
          description: "Async handler không có try/catch. db.findUser() throw → UnhandledPromiseRejection → server treo.",
          fix: "try {\n  const user = await db.findUser(req.params.id);\n  res.json(user);\n} catch (err) { next(err); }",
        },
        {
          severity: "high",
          pattern_id: "unhandled_rejection",
          line_range: "12-15",
          description: "Route thứ hai có 2 await không được bảo vệ. Bất kỳ await nào fail → unhandled rejection.",
          fix: "Dùng express-async-errors package hoặc wrap mọi async handler.",
        },
      ],
      docs_used: [
        { id: "d007", title: "Express Error Handling", category: "express" },
        { id: "d022", title: "Unhandled Promise Rejection", category: "async" },
        { id: "d031", title: "Async Middleware Pattern", category: "express" },
      ],
      explanation: "Express 4 không tự catch async errors. Khi async handler throw, Express không nhận error — thành <strong>UnhandledPromiseRejection</strong>.\n\nFix: wrap bằng try/catch + next(err), hoặc dùng package <strong>express-async-errors</strong>, hoặc upgrade lên Express 5.",
    },
  },
  {
    title: "sequential_awaits — dashboard 3 awaits",
    code: `// Bug: sequential awaits — performance anti-pattern
// Source: nodebestpractices

async function getDashboard(userId) {
  // 3 queries chạy tuần tự, không cần thiết
  const user          = await db.users.findById(userId);
  const orders        = await db.orders.findByUser(userId);
  const notifications = await db.notifications.findByUser(userId);

  return { user, orders, notifications };
}

// t=0ms   → user query
// t=120ms → orders query
// t=240ms → notifications query
// t=360ms → done  (thay vì ~120ms với Promise.all)`,
    response: {
      issues: [
        {
          severity: "low",
          pattern_id: "sequential_awaits",
          line_range: "6-8",
          description: "3 await độc lập chạy tuần tự. Không phụ thuộc nhau → có thể chạy song song, giảm latency ~3x.",
          fix: "const [user, orders, notifications] = await Promise.all([\n  db.users.findById(userId),\n  db.orders.findByUser(userId),\n  db.notifications.findByUser(userId)\n]);",
        },
      ],
      docs_used: [
        { id: "d009", title: "Promise.all Concurrency", category: "async" },
        { id: "d033", title: "Sequential vs Parallel Async", category: "performance" },
        { id: "d041", title: "Dashboard Query Patterns", category: "patterns" },
      ],
      explanation: "Pattern <strong>Sequential Awaits</strong> không crash nhưng là performance anti-pattern. Khi Promises không phụ thuộc nhau, dùng await tuần tự lãng phí thời gian.\n\n<strong>Promise.all()</strong> chạy concurrently: latency = max(t1,t2,t3) thay vì t1+t2+t3. Dashboard 3 queries ~120ms mỗi cái: 360ms → 120ms.",
    },
  },
  {
    title: "context_loss_this — class method + express",
    code: `// Bug: mất this khi truyền class method vào Express
// Source: express-async-errors/issues/3

class UserController {
  constructor() {
    this.db = new Database();
    this.cache = new RedisCache();
  }

  async getUser(req, res) {
    // this.db = undefined khi Express gọi!
    const cached = await this.cache.get(req.params.id);
    if (cached) return res.json(cached);
    const user = await this.db.findById(req.params.id);
    res.json(user);
  }
}

const ctrl = new UserController();
app.get('/user/:id', ctrl.getUser);   // mất this!
app.get('/users',    ctrl.listUsers); // mất this!`,
    response: {
      issues: [
        {
          severity: "high",
          pattern_id: "context_loss_this",
          line_range: "19-20",
          description: "ctrl.getUser truyền như function reference — this bị mất khi Express gọi. this.db và this.cache → undefined → TypeError.",
          fix: "app.get('/user/:id', ctrl.getUser.bind(ctrl));\n// hoặc arrow:\napp.get('/user/:id', (req,res) => ctrl.getUser(req,res));",
        },
        {
          severity: "medium",
          pattern_id: "context_loss_this",
          line_range: "11-14",
          description: "this.cache và this.db trong method body sẽ fail khi this bị mất.",
          fix: "Bind trong constructor:\nthis.getUser = this.getUser.bind(this);",
        },
      ],
      docs_used: [
        { id: "d011", title: "this Binding JavaScript", category: "fundamentals" },
        { id: "d027", title: "Class Method Context", category: "oop" },
        { id: "d035", title: "Express Route Handlers", category: "express" },
      ],
      explanation: "JavaScript <strong>this</strong> phụ thuộc vào cách function được <em>gọi</em>, không phải nơi định nghĩa. <code>ctrl.getUser</code> chỉ là function reference thuần — không có context. Express gọi nó: this = undefined (strict mode).\n\nFix: <strong>.bind(ctrl)</strong> khi đăng ký route, hoặc bind tất cả methods trong constructor.",
    },
  },
  // ── Live mode sample codes ──────────────────────────────────────────────────
  {
    title: "race_condition — db stock decrement",
    liveOnly: true,
    code: `// Race condition: concurrent stock decrement
async function purchaseItem(productId, userId) {
  const stock = await db.getStock(productId);
  if (stock <= 0) throw new Error("Out of stock");

  // Race window: another request reads stock = 1 here
  await db.setStock(productId, stock - 1);
  await db.createOrder({ productId, userId });
}`,
    response: null,
  },
  {
    title: "event_loop_blocking — readFileSync in loop",
    liveOnly: true,
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
    response: null,
  },
  {
    title: "zalgo — sync/async mixed callback",
    liveOnly: true,
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
    response: null,
  },
  {
    title: "resource_exhaustion — Promise.all unlimited",
    liveOnly: true,
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
    response: null,
  },
  {
    title: "callback_hell — nested 4 levels deep",
    liveOnly: true,
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
    response: null,
  },
  {
    title: "missing_error_handler — stream pipe",
    liveOnly: true,
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
    response: null,
  },
  {
    title: "singleton_race — lazy init shared state",
    liveOnly: true,
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

// Concurrent callers
app.get('/users', async (req, res) => {
  const conn = await getConnection();
  const users = await conn.query('SELECT * FROM users');
  res.json(users);
});`,
    response: null,
  },
  {
    title: "event_loop_ordering — nextTick vs setTimeout",
    liveOnly: true,
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
    response: null,
  },
];
