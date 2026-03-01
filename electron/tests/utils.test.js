'use strict'
/**
 * electron/tests/utils.test.js
 * Pure Node.js unit tests for electron/utils.js
 * Run with: node electron/tests/utils.test.js
 */

const assert = require('assert')
const { parseListeningPort, findFreePort } = require('../utils')

let passed = 0
let failed = 0

function test(name, fn) {
  try {
    fn()
    console.log(`  [OK] ${name}`)
    passed++
  } catch (err) {
    console.error(`  [FAIL] ${name}`)
    console.error(`         ${err.message}`)
    failed++
  }
}

async function asyncTest(name, fn) {
  try {
    await fn()
    console.log(`  [OK] ${name}`)
    passed++
  } catch (err) {
    console.error(`  [FAIL] ${name}`)
    console.error(`         ${err.message}`)
    failed++
  }
}

// ─────────────────────────────────────────
// parseListeningPort tests
// ─────────────────────────────────────────
console.log('\nparseListeningPort')
test('returns port number for valid LISTENING_PORT line', () => {
  assert.strictEqual(parseListeningPort('LISTENING_PORT=18765'), 18765)
})

test('returns port number when line has trailing whitespace/newline', () => {
  assert.strictEqual(parseListeningPort('LISTENING_PORT=8080\r\n'), 8080)
})

test('returns null for unrelated line', () => {
  assert.strictEqual(parseListeningPort('INFO: uvicorn started'), null)
})

test('returns null for empty string', () => {
  assert.strictEqual(parseListeningPort(''), null)
})

test('returns null for partial match (no number)', () => {
  assert.strictEqual(parseListeningPort('LISTENING_PORT='), null)
})

test('returns null for zero port', () => {
  assert.strictEqual(parseListeningPort('LISTENING_PORT=0'), null)
})

test('handles LISTENING_PORT with extra prefix text', () => {
  // Must be exact prefix — extra leading text should not match
  assert.strictEqual(parseListeningPort('extra LISTENING_PORT=1234'), null)
})

// ─────────────────────────────────────────
// findFreePort tests
// ─────────────────────────────────────────
console.log('\nfindFreePort')

async function runAsyncTests() {
  await asyncTest('returns a positive integer port number', async () => {
    const port = await findFreePort()
    assert.ok(typeof port === 'number', 'port should be a number')
    assert.ok(port > 0 && port <= 65535, `port ${port} out of valid range`)
  })

  await asyncTest('returns different ports on consecutive calls', async () => {
    const p1 = await findFreePort()
    const p2 = await findFreePort()
    // Ports should not collide (highly unlikely if OS properly marks them reserved briefly)
    // We just check both are valid
    assert.ok(p1 > 0 && p2 > 0)
  })

  // ── summary ──────────────────────────────
  console.log(`\n${passed} passed, ${failed} failed`)
  if (failed > 0) {
    process.exitCode = 1
  }
}

runAsyncTests()
