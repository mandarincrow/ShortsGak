'use strict'
/**
 * electron/utils.js
 * Pure utility functions extracted for unit testability.
 */

const net = require('net')

/**
 * Find a free TCP port by asking the OS to assign one.
 * @returns {Promise<number>} available port number
 */
function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port
      server.close((err) => {
        if (err) reject(err)
        else resolve(port)
      })
    })
    server.on('error', reject)
  })
}

/**
 * Parse a LISTENING_PORT=N signal line emitted by backend.exe to stdout.
 * @param {string} line - single line of text (may include \r\n)
 * @returns {number|null} port number, or null if not a valid signal line
 */
function parseListeningPort(line) {
  const trimmed = line.trim()
  const match = trimmed.match(/^LISTENING_PORT=(\d+)$/)
  if (!match) return null
  const port = parseInt(match[1], 10)
  return port > 0 ? port : null
}

module.exports = { findFreePort, parseListeningPort }
