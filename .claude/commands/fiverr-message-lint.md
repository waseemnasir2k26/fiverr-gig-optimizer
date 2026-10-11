# Fiverr Message Lint

Check a message to a Fiverr buyer before it is sent.

1. Run `fiverr-gig lint --text "<message>"` (or pipe a file with `fiverr-gig lint -`).
2. For each finding, rewrite the sentence so it no longer asks for or offers off-platform contact or payment. Use the suggestions the tool prints (for example "my fee" instead of naming a payment method, "message me here" instead of naming a chat app).
3. Re-run until clean. A clean result is not a guarantee: Fiverr does not publish its filter.
4. Never use disguised spellings such as "p.a.y" or "e m a i l". They look like evasion; the tool flags them as worse than the plain word.
5. If the honest meaning of the message is to move the buyer off Fiverr, do not send it. Fiverr's terms keep communication and payment on the platform.

When the user quotes a price in a message, remember Fiverr keeps 20% and the buyer also pays a service fee: `fiverr-gig price --gross <price>`.
