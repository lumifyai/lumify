import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { verifyWebhook, WebhookSignatureError } from "../dist/webhook-signature.js";
import { createHmac } from "node:crypto";

const SECRET = "whsec_test_1234567890";
const BODY = '{"event_id":42,"status":"final"}';

function sign(secret, ts, body) {
  return createHmac("sha256", secret).update(`${ts}.${body}`).digest("hex");
}

describe("verifyWebhook()", () => {
  test("accepts a correctly-signed, fresh delivery", async () => {
    const ts = Math.floor(Date.now() / 1000);
    const sig = sign(SECRET, ts, BODY);
    await assert.doesNotReject(verifyWebhook(SECRET, `t=${ts},v1=${sig}`, BODY));
  });

  test("rejects a tampered body", async () => {
    const ts = Math.floor(Date.now() / 1000);
    const sig = sign(SECRET, ts, BODY);
    await assert.rejects(verifyWebhook(SECRET, `t=${ts},v1=${sig}`, BODY + "tampered"), WebhookSignatureError);
  });

  test("rejects the wrong signing secret", async () => {
    const ts = Math.floor(Date.now() / 1000);
    const sig = sign("whsec_wrong", ts, BODY);
    await assert.rejects(verifyWebhook(SECRET, `t=${ts},v1=${sig}`, BODY), WebhookSignatureError);
  });

  test("rejects a stale timestamp outside the tolerance window", async () => {
    const ts = Math.floor(Date.now() / 1000) - 1000; // 1000s old, default tolerance 300s
    const sig = sign(SECRET, ts, BODY);
    await assert.rejects(verifyWebhook(SECRET, `t=${ts},v1=${sig}`, BODY), WebhookSignatureError);
  });

  test("respects a custom toleranceSeconds", async () => {
    const ts = Math.floor(Date.now() / 1000) - 1000;
    const sig = sign(SECRET, ts, BODY);
    await assert.doesNotReject(verifyWebhook(SECRET, `t=${ts},v1=${sig}`, BODY, { toleranceSeconds: 2000 }));
  });

  test("rejects a malformed header", async () => {
    await assert.rejects(verifyWebhook(SECRET, "not-a-valid-header", BODY), WebhookSignatureError);
    await assert.rejects(verifyWebhook(SECRET, "t=abc,v1=xyz", BODY), WebhookSignatureError);
  });
});
