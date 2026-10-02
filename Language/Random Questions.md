𝗖𝗢𝗥𝗘 𝗝𝗔𝗩𝗔:
 1. A HashMap key's hashCode changes after insertion. What does get() return for that key?
 2. Double-checked locking singleton, no volatile. What can the second thread see?
 3. ThreadLocal inside a thread pool. Where is the leak, and what one line stops it?
 4. Two threads increment a shared long, no synchronized, no atomic. Two different reasons the result is wrong.
 5. 30 GB heap, 10 ms pause budget. G1 or ZGC, and why?

𝗦𝗣𝗥𝗜𝗡𝗚:
 6. @ Transactional on a private method. What actually happens?
 7. A @ Transactional method calls a REQUIRES_NEW method in the same class. How many transactions run?
 8. Two beans need each other through constructor injection. What does Spring Boot 3 do at startup?
 9. 500 outbound HTTP calls a second. RestTemplate or WebClient, and what breaks with the other?
10. A checked exception is thrown inside a @ Transactional method. Does it roll back?

𝗞𝗔𝗙𝗞𝗔:
 11. Consumer processes a message, crashes before committing the offset. What does the next consumer see?
 12. You add partitions to a live topic. What happens to per-key ordering?
 13. Producer retries after a timeout and the message lands twice. Which setting stops that?

𝗗𝗔𝗧𝗔𝗕𝗔𝗦𝗘 𝗔𝗡𝗗 𝗝𝗣𝗔:
 14. 200 orders on a page, 201 queries in the log. Name it, give two fixes.
 15. Two transactions read one row, both update it, one update vanishes. What prevents it?
 16. Index on (status, created_at). The query filters on created_at only. Does it help?
 17. Hibernate second-level cache, two app instances. Why does instance B serve stale data?

𝗦𝗬𝗦𝗧𝗘𝗠 𝗗𝗘𝗦𝗜𝗚𝗡:
 18. Rate limiter for a public API on 40 servers. Where does the counter live, and where is the race?
 19. A client retries a payment call after a timeout. How do you guarantee one charge?
 20. Notification service, email plus SMS plus push. SMS provider dies for 20 minutes. What happens to email and push?
