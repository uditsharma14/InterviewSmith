# Java 21 Core Concepts — Interview Prep, Basic to Staff Level (with Code & Sources)

> **Target level:** Basic → Staff (graduated — see below) · **Baseline:** Java/JDK 21 (LTS); where a JDK 21 preview feature was later finalized, changed, or withdrawn, the later JDK version is named explicitly · Resilience4j section targets Resilience4j 2.x with the Spring Boot 3 starter · **Last verified:** 2026-10-02 · **Prerequisites:** core Java syntax for the Basic section; [OOP Concepts](../Language/OOP_Concepts_Interview_Prep.md) helpful for sealed types; [Java Concurrency](../Language/Java_Concurrency_Interview_Prep.md) for the virtual-thread questions

How to use this: each question has **the answer the way I'd actually say it out loud** in an interview, a **code snippet** to back it up, and **where the follow-up goes in a Staff-level loop**. The Java 21 sections cover the language and library features that shipped as final in (or were finalized by) JDK 21 — the things an interviewer means by "do you know modern Java?" The last section is applied rather than language-level: a production Resilience4j configuration walked through setting by setting, because "how do you protect a downstream call?" is one of the most common follow-ups in a Java backend loop. Virtual threads are only summarized here; the deep treatment lives in [Java Concurrency](../Language/Java_Concurrency_Interview_Prep.md), and the architecture-level view of circuit breaker/bulkhead/retry lives in [Microservices Architecture Patterns Q14](../Microservices%20%26%20Architecture%20Patterns/Microservices_Architecture_Patterns_Interview_Prep.md#14-explain-circuit-breaker-bulkhead-and-retry-as-a-combined-resilience-strategy).

<!-- toc -->
## Table of Contents

- [Basic](#basic)
  - [1. What Are the Headline Features of Java 21, and Why Does It Matter That It's an LTS Release?](#1-what-are-the-headline-features-of-java-21-and-why-does-it-matter-that-its-an-lts-release)
  - [2. What Is a Record, and When Would You Use One?](#2-what-is-a-record-and-when-would-you-use-one)
  - [3. What Do `var`, Text Blocks, and Switch Expressions Give You?](#3-what-do-var-text-blocks-and-switch-expressions-give-you)
  - [4. What Is Pattern Matching for `instanceof`?](#4-what-is-pattern-matching-for-instanceof)
- [Intermediate](#intermediate)
  - [5. What Are Sealed Classes and Interfaces?](#5-what-are-sealed-classes-and-interfaces)
  - [6. How Does Pattern Matching for `switch` Work in Java 21?](#6-how-does-pattern-matching-for-switch-work-in-java-21)
  - [7. What Are Record Patterns?](#7-what-are-record-patterns)
  - [8. What Are Sequenced Collections?](#8-what-are-sequenced-collections)
  - [9. What Are Virtual Threads, in One Interview Answer?](#9-what-are-virtual-threads-in-one-interview-answer)
- [Staff Level](#staff-level)
  - [10. Sealed Types + Records + Pattern Matching vs. Polymorphism — When Do You Use Which?](#10-sealed-types--records--pattern-matching-vs-polymorphism--when-do-you-use-which)
  - [11. What Would You Check Before Upgrading a Spring Boot Service From Java 17 to 21?](#11-what-would-you-check-before-upgrading-a-spring-boot-service-from-java-17-to-21)
- [Applied: Resilience4j Configuration for a Downstream Dependency](#applied-resilience4j-configuration-for-a-downstream-dependency)
  - [12. Walk Me Through Your Resilience4j Configuration for a Downstream Call](#12-walk-me-through-your-resilience4j-configuration-for-a-downstream-call)
  - [13. Explain the Bulkhead and Rate Limiter Settings — and Why You Need Both](#13-explain-the-bulkhead-and-rate-limiter-settings--and-why-you-need-both)
  - [14. Explain the Circuit Breaker Settings and State Machine](#14-explain-the-circuit-breaker-settings-and-state-machine)
  - [15. Explain the Retry Settings — What Do You Retry, and What Don't You?](#15-explain-the-retry-settings--what-do-you-retry-and-what-dont-you)
  - [16. In What Order Do the Resilience4j Aspects Run, and Why Does It Matter?](#16-in-what-order-do-the-resilience4j-aspects-run-and-why-does-it-matter)
  - [17. How Would You Summarize Your Resilience Setup in Under a Minute?](#17-how-would-you-summarize-your-resilience-setup-in-under-a-minute)
- [Sources & Further Reading — Consolidated](#sources--further-reading--consolidated)

<!-- /toc -->

---

## Basic

### 1. What Are the Headline Features of Java 21, and Why Does It Matter That It's an LTS Release?

**Answer:**

"Java 21 is a long-term-support release, so it's the version most companies move to from 17, and the one interviewers assume when they say 'modern Java.' The final, production-ready features that matter most are: **virtual threads** (JEP 444), **pattern matching for `switch`** (JEP 441), **record patterns** (JEP 440), **sequenced collections** (JEP 431), and **generational ZGC** (JEP 439). Pattern matching for `switch` and record patterns are the payoff of a multi-release story — records (final in 16) and sealed classes (final in 17) give you closed, transparent data types, and 21 finally gives you the syntax to take them apart exhaustively.

Java 21 also shipped several features as *preview* only — string templates, unnamed patterns and variables, unnamed classes and instance main methods, scoped values, and structured concurrency. Preview features need `--enable-preview` at both compile time and run time, and their API can change or disappear, so I wouldn't use them in production code on 21."

**Code:**

```text
Final in JDK 21 (production-ready)          Preview / incubator in JDK 21 (not production)
-----------------------------------          ---------------------------------------------
JEP 444  Virtual Threads                     JEP 430  String Templates           -> withdrawn (absent from JDK 23)
JEP 441  Pattern Matching for switch         JEP 443  Unnamed Patterns/Variables -> final in JDK 22 (JEP 456)
JEP 440  Record Patterns                     JEP 445  Unnamed Classes / instance main -> final in JDK 25 (JEP 512)
JEP 431  Sequenced Collections               JEP 446  Scoped Values              -> final in JDK 25 (JEP 506)
JEP 439  Generational ZGC (opt-in)           JEP 453  Structured Concurrency     -> still preview after 21
                                             JEP 442  Foreign Function & Memory  -> final in JDK 22 (JEP 454)
```

**Follow-up:**

- *"Would you turn on `--enable-preview` in production?"* — No. Preview features are fully implemented but not permanent; string templates are the cautionary example — previewed in 21 and 22, then dropped entirely. Code written against them had to be rewritten.
- *"What did you have to change moving from 17 to 21?"* — Usually very little at the language level, since 21 is additive. The real work is dependency upgrades (build plugins, bytecode libraries like ByteBuddy/ASM, Lombok, Mockito) that need to understand the newer class-file version, plus deciding whether to adopt virtual threads and generational ZGC — both opt-in, both needing load-testing rather than a flag flip.

**Source:** [OpenJDK — JDK 21 feature list](https://openjdk.org/projects/jdk/21/), [JEP 12 — Preview Features](https://openjdk.org/jeps/12)

---

### 2. What Is a Record, and When Would You Use One?

**Answer:**

"A record is a class whose whole purpose is to carry data. You declare the components in the header, and the compiler generates a private final field per component, a canonical constructor, accessor methods named after the components — `amount()`, not `getAmount()` — and `equals`, `hashCode`, and `toString` based on all components. Records are implicitly final, extend `java.lang.Record`, and can't declare extra instance fields, but they can implement interfaces and have static fields, static methods, and instance methods.

I use them for DTOs, API request/response bodies, value objects, map keys, and multi-value returns. The compact canonical constructor is where validation and normalization go. One caveat: a record is only *shallowly* immutable — a `List` component can still be mutated by whoever holds the reference, so I copy it with `List.copyOf` in the constructor."

**Code:**

Compilable example:

```java
import java.math.BigDecimal;
import java.util.Objects;

public record Money(BigDecimal amount, String currency) {
    // Compact canonical constructor: runs before the fields are assigned,
    // so reassigning a parameter here changes what gets stored.
    public Money {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currency, "currency");
        if (amount.signum() < 0) throw new IllegalArgumentException("negative amount");
        currency = currency.toUpperCase();
    }

    public Money plus(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(amount.add(other.amount), currency);
    }

    public static void main(String[] args) {
        Money a = new Money(new BigDecimal("10.00"), "usd");
        Money b = new Money(new BigDecimal("10.00"), "USD");
        System.out.println(a);                  // Money[amount=10.00, currency=USD]
        System.out.println(a.equals(b));        // true: component-wise equals after normalization
        System.out.println(a.plus(b).amount()); // 20.00
    }
}
```

**Follow-up:**

- *"Can a record be a JPA entity?"* — No. The Jakarta Persistence spec requires an entity to be non-final with a no-arg constructor and mutable state for dirty checking; records are final with only a canonical constructor. Records work well as query projections and DTOs instead.
- *"`equals` on a record with a `BigDecimal` component?"* — It delegates to `BigDecimal.equals`, which compares scale: `10.0` and `10.00` are *not* equal. Normalize scale in the compact constructor if value equality should ignore it.

**Source:** [JEP 395 — Records](https://openjdk.org/jeps/395), [`java.lang.Record` Javadoc (JDK 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Record.html)

---

### 3. What Do `var`, Text Blocks, and Switch Expressions Give You?

**Answer:**

"These are the pre-21 syntax features every Java 21 codebase uses. **`var`** (Java 10) is local-variable type inference — the type is still static and fixed at compile time; it just isn't written out. I use it when the right-hand side makes the type obvious, and avoid it when it hides something important, like whether a result is a `List` or a `Stream`. It's only for local variables, not fields, parameters, or return types.

**Text blocks** (Java 15) are multi-line string literals delimited by triple quotes. Incidental indentation is stripped based on the least-indented line, which makes embedded JSON, SQL, or HTML readable.

**Switch expressions** (Java 14) let `switch` produce a value. The arrow form has no fall-through, and when it's used as an expression the compiler requires it to be exhaustive. `yield` returns a value from a block-bodied case. These are the foundation pattern matching for `switch` builds on in 21."

**Code:**

Compilable example:

```java
import java.time.DayOfWeek;

public class ModernSyntax {
    static int letters(DayOfWeek day) {
        return switch (day) {                       // expression: must be exhaustive over the enum
            case MONDAY, FRIDAY, SUNDAY -> 6;
            case TUESDAY -> 7;
            case THURSDAY, SATURDAY -> 8;
            case WEDNESDAY -> {
                int n = "WEDNESDAY".length();
                yield n;                            // yield, not return, inside a block case
            }
        };
    }

    public static void main(String[] args) {
        var json = """
                {
                  "id": 42,
                  "status": "ACTIVE"
                }
                """;                                // var infers String; indentation is stripped
        System.out.print(json);
        System.out.println(letters(DayOfWeek.WEDNESDAY)); // 9
    }
}
```

**Follow-up:**

- *"Does `var` make Java dynamically typed?"* — No. `var x = 1;` makes `x` an `int` forever; assigning a `String` later is a compile error.
- *"Gotcha with `var` and diamond?"* — `var list = new ArrayList<>();` infers `ArrayList<Object>`, which is rarely what you meant. Give the type argument on one side.

**Source:** [JEP 286 — Local-Variable Type Inference](https://openjdk.org/jeps/286), [JEP 378 — Text Blocks](https://openjdk.org/jeps/378), [JEP 361 — Switch Expressions](https://openjdk.org/jeps/361)

---

### 4. What Is Pattern Matching for `instanceof`?

**Answer:**

"Before Java 16 you'd test a type with `instanceof` and then cast on the next line. Pattern matching for `instanceof` combines the test and the binding: `if (obj instanceof String s)` declares `s` already typed as `String`, and it's only in scope where the match is definitely true. Flow scoping means it also works with negation: after `if (!(obj instanceof String s)) return;`, `s` is in scope for the rest of the method. It removes a whole class of copy-paste cast bugs, and it's the simplest form of the patterns that `switch` uses in 21."

**Code:**

Compilable example:

```java
public class InstanceofPatterns {
    static int lengthOrZero(Object obj) {
        if (!(obj instanceof String s)) {
            return 0;
        }
        return s.length();                  // s is in scope: the early return proves the match
    }

    public static void main(String[] args) {
        Object o = "hello";
        if (o instanceof String s && s.length() > 3) {  // s usable on the right of &&
            System.out.println(s.toUpperCase());        // HELLO
        }
        System.out.println(lengthOrZero(42));           // 0
    }
}
```

**Follow-up:**

- *"Why does `o instanceof String s || s.isEmpty()` not compile?"* — With `||`, the right-hand side runs exactly when the match *failed*, so `s` isn't definitely assigned there.

**Source:** [JEP 394 — Pattern Matching for instanceof](https://openjdk.org/jeps/394)

---

## Intermediate

### 5. What Are Sealed Classes and Interfaces?

**Answer:**

"A sealed class or interface restricts which classes may directly extend or implement it, using a `permits` clause. Every permitted subclass must itself say how it continues the hierarchy: `final`, `sealed` with its own `permits`, or `non-sealed` to reopen it. Records are implicitly final, so they're a natural fit as the leaves.

The point isn't access control — it's telling the compiler that the set of subtypes is *closed*. That's what lets a `switch` over a sealed type be exhaustive without a `default`. If someone adds a new permitted subtype, every switch that doesn't handle it stops compiling, instead of falling silently into a `default` branch at runtime. That's what I want for things like payment results, domain events, or command types."

**Code:**

Compilable example:

```java
public class Shapes {
    sealed interface Shape permits Circle, Square, Rectangle {}
    record Circle(double radius) implements Shape {}
    record Square(double side) implements Shape {}
    record Rectangle(double width, double height) implements Shape {}

    // Exhaustive with no default, because Shape is sealed.
    // Adding a fourth permitted subtype makes this a compile error until it's handled.
    static double area(Shape shape) {
        return switch (shape) {
            case Circle c -> Math.PI * c.radius() * c.radius();
            case Square s -> s.side() * s.side();
            case Rectangle r -> r.width() * r.height();
        };
    }

    public static void main(String[] args) {
        System.out.println(area(new Square(3)));       // 9.0
        System.out.println(area(new Rectangle(2, 5))); // 10.0
    }
}
```

**Follow-up:**

- *"Where must permitted subclasses live?"* — In the same module as the sealed type, or in the same package if it's in the unnamed module. If they're all in the same source file, the `permits` clause can be omitted and is inferred.
- *"What does `non-sealed` cost you?"* — Exhaustiveness for that branch. Anyone can extend a `non-sealed` subtype, so a switch has to handle it as a whole (by its type), not by enumerating its subclasses.

**Source:** [JEP 409 — Sealed Classes](https://openjdk.org/jeps/409)

---

### 6. How Does Pattern Matching for `switch` Work in Java 21?

**Answer:**

"From Java 21, `case` labels can be type patterns, not just constants. `case Integer i ->` matches when the selector is an `Integer` and binds `i`. A `when` clause adds a guard: `case String s when s.isBlank()`. The selector can be any reference type, and you can write `case null` explicitly — without it, a `switch` still throws `NullPointerException` on null, same as before.

Two compile-time rules matter. **Exhaustiveness**: a pattern switch has to cover every possible value — via a `default`, a total pattern, or all permitted subtypes of a sealed type. **Dominance**: a case can't come after a case that already matches everything it would match, so a guarded `case Integer i when i > 100` has to come before the unguarded `case Integer i`, otherwise it's a compile error. Cases are tested top to bottom."

**Code:**

Compilable example:

```java
public class Describe {
    static String describe(Object o) {
        return switch (o) {
            case null -> "null";                            // explicit null handling
            case Integer i when i > 100 -> "big int " + i;  // guarded case must precede unguarded one
            case Integer i -> "int " + i;
            case String s when s.isBlank() -> "blank string";
            case String s -> "string of length " + s.length();
            default -> "something else: " + o.getClass().getSimpleName();
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(null));  // null
        System.out.println(describe(500));   // big int 500
        System.out.println(describe(7));     // int 7
        System.out.println(describe("  "));  // blank string
        System.out.println(describe(2.5));   // something else: Double
    }
}
```

**Follow-up:**

- *"A sealed switch compiled without a default — what if a new subtype shows up at runtime because a library was recompiled separately?"* — The compiler inserts a synthetic default that throws `MatchException`. You get a loud failure, not a silent wrong branch.
- *"Is this just a nicer `if/else instanceof` chain?"* — Mostly, but the exhaustiveness check is the real value. An `if` chain has no compile-time guarantee you covered every case.

**Source:** [JEP 441 — Pattern Matching for switch](https://openjdk.org/jeps/441)

---

### 7. What Are Record Patterns?

**Answer:**

"A record pattern deconstructs a record into its components right in the match: `if (o instanceof Point(int x, int y))` tests the type and binds `x` and `y` through the accessors in one step. They nest, so `case Mul(Num(var a), Num(var b))` matches only a multiplication of two literal numbers. `var` is allowed for component types. Combined with sealed interfaces and switch, this gives you exhaustive, structural matching over a tree of data — the kind of thing that used to need the Visitor pattern."

**Code:**

Compilable example:

```java
public class RecordPatterns {
    record Point(int x, int y) {}

    sealed interface Expr permits Num, Add, Mul {}
    record Num(int value) implements Expr {}
    record Add(Expr left, Expr right) implements Expr {}
    record Mul(Expr left, Expr right) implements Expr {}

    static int eval(Expr e) {
        return switch (e) {
            case Num(int v) -> v;
            case Add(Expr l, Expr r) -> eval(l) + eval(r);
            case Mul(Num(var a), Num(var b)) -> a * b;   // nested pattern, more specific first
            case Mul(Expr l, Expr r) -> eval(l) * eval(r);
        };
    }

    public static void main(String[] args) {
        Object o = new Point(3, 4);
        if (o instanceof Point(int x, int y)) {
            System.out.println(x + y);                   // 7
        }
        Expr e = new Add(new Num(2), new Mul(new Num(3), new Num(4)));
        System.out.println(eval(e));                     // 14
    }
}
```

**Follow-up:**

- *"Does a record pattern match `null`?"* — No. A record pattern never matches `null`. A `null` selector still throws `NullPointerException` unless there's a `case null`, and a `null` *component* simply fails the nested pattern, so the match falls through to a later case. `Mul(Num(var a), Num(var b))` doesn't match `new Mul(null, null)`, but `Mul(Expr l, Expr r)` does, because a type pattern that covers the component's declared type also matches `null`.
- *"What about components you don't care about?"* — In 21 you have to name them (or use `var`). The unnamed pattern `_`, as in `case Add(Num n, _)`, was preview in 21 and became final in JDK 22 (JEP 456).

**Source:** [JEP 440 — Record Patterns](https://openjdk.org/jeps/440), [JEP 456 — Unnamed Variables & Patterns](https://openjdk.org/jeps/456)

---

### 8. What Are Sequenced Collections?

**Answer:**

"Before 21 there was no common type for 'a collection with a defined encounter order.' Getting the last element was `list.get(list.size() - 1)` for a `List`, a full iteration for a `LinkedHashSet`, and `deque.getLast()` for a `Deque` — three different APIs for the same idea. JEP 431 added three interfaces — `SequencedCollection`, `SequencedSet`, and `SequencedMap` — retrofitted onto `List`, `Deque`, `LinkedHashSet`, `SortedSet`, `LinkedHashMap`, and `SortedMap`. They give a uniform `getFirst`/`getLast`/`addFirst`/`addLast`/`removeFirst`/`removeLast` plus `reversed()`. On maps: `firstEntry`, `lastEntry`, `pollFirstEntry`, `putFirst`, and so on.

`reversed()` returns a *view*, not a copy — writes through the view affect the original. And these are default methods, so an unmodifiable collection like `List.of(...)` still throws `UnsupportedOperationException` on `addFirst`."

**Code:**

Compilable example:

```java
import java.util.*;

public class Sequenced {
    public static void main(String[] args) {
        List<String> list = new ArrayList<>(List.of("a", "b", "c"));
        System.out.println(list.getFirst() + list.getLast()); // ac
        list.addFirst("z");
        System.out.println(list.reversed());                  // [c, b, a, z]: a view, not a copy

        LinkedHashSet<Integer> set = new LinkedHashSet<>(List.of(1, 2, 3));
        System.out.println(set.getLast());                    // 3, previously needed full iteration

        LinkedHashMap<String, Integer> map = new LinkedHashMap<>();
        map.put("one", 1);
        map.put("two", 2);
        System.out.println(map.firstEntry());                 // one=1
        System.out.println(map.pollLastEntry());              // two=2 (removed)
        System.out.println(map);                              // {one=1}

        try {
            List.of("x", "y").addFirst("w");
        } catch (UnsupportedOperationException ex) {
            System.out.println("unmodifiable list rejects addFirst");
        }
    }
}
```

**Follow-up:**

- *"Is `HashSet` a `SequencedCollection`?"* — No. It has no defined encounter order. That's the point of the type: it lets an API demand order in its signature instead of documenting it.
- *"Any migration risk?"* — Rarely, but yes. A class that implemented both `List` and `Deque`, or a library that already defined `getFirst()`/`reversed()` with a different return type, can hit source or binary conflicts. Check this during the 21 upgrade.

**Source:** [JEP 431 — Sequenced Collections](https://openjdk.org/jeps/431), [`SequencedCollection` Javadoc (JDK 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/SequencedCollection.html)

---

### 9. What Are Virtual Threads, in One Interview Answer?

**Answer:**

"Virtual threads, final in Java 21, are `java.lang.Thread` instances scheduled by the JVM rather than mapped one-to-one to OS threads. Many virtual threads are multiplexed over a small pool of carrier platform threads. When a virtual thread blocks on I/O — a socket read, a JDBC call, a `sleep` — the JVM unmounts it from its carrier, and the carrier picks up other work. So you can write plain blocking, thread-per-request code and still handle tens of thousands of concurrent requests that are mostly waiting.

They help throughput for I/O-bound work. They don't make CPU-bound code faster, they shouldn't be pooled — create one per task — and in JDK 21 a virtual thread that blocks while inside a `synchronized` block *pins* its carrier, which can starve the scheduler. JDK 24 fixed most of that pinning (JEP 491). In Spring Boot 3.2+, `spring.threads.virtual.enabled=true` switches Tomcat and the default task executors to virtual threads."

**Code:**

Compilable example:

```java
import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.stream.IntStream;

public class VirtualThreads {
    public static void main(String[] args) throws InterruptedException {
        long start = System.nanoTime();
        // One new virtual thread per task; close() at the end of try waits for all of them
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, 10_000).forEach(i -> executor.submit(() -> {
                Thread.sleep(Duration.ofSeconds(1)); // parks the virtual thread, frees the carrier
                return i;
            }));
        }
        System.out.printf("10,000 one-second blocking tasks took ~%d ms%n",
                (System.nanoTime() - start) / 1_000_000);

        Thread vt = Thread.ofVirtual().name("vt-1").start(() ->
                System.out.println("isVirtual=" + Thread.currentThread().isVirtual())); // isVirtual=true
        vt.join();
    }
}
```

**Follow-up:**

The Staff-level questions — pinning, `ThreadLocal` cost per virtual thread, why you replace pool limits with semaphores, and virtual threads vs. reactive — are covered in [Java Concurrency Q20 and Q21](../Language/Java_Concurrency_Interview_Prep.md#20-compare-platform-threads-virtual-threads-reactive-execution-and-asynchronous-futures). One point that ties into the Resilience4j section below: with virtual threads, thread exhaustion stops being what protects your downstream. A fixed Tomcat pool of 200 used to cap concurrent outbound calls by accident. With virtual threads, nothing does, so an explicit bulkhead or semaphore becomes *more* important.

**Source:** [JEP 444 — Virtual Threads](https://openjdk.org/jeps/444), [JEP 491 — Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491), [Spring Boot reference — Virtual Threads](https://docs.spring.io/spring-boot/reference/features/spring-application.html#features.spring-application.virtual-threads)

---

## Staff Level

### 10. Sealed Types + Records + Pattern Matching vs. Polymorphism — When Do You Use Which?

**Answer:**

"This is the 'data-oriented programming' question. Classic OO puts behavior on the type: `shape.area()`, each subclass overrides it. That's best when the set of *operations* is fixed and the set of *types* grows — adding a type is one new class, and no existing code changes. Sealed types plus pattern-matching `switch` invert it: the set of *types* is fixed and closed, and *operations* are written outside the types as exhaustive switches. That's best when the operations grow — validation, serialization, pricing, auditing — and you don't want every one of them stuffed into the domain classes. Adding a type is then a compile error at every switch, which is the feature: the compiler gives you a to-do list.

So I ask which axis changes more. Payment outcomes, workflow states, AST nodes, and event types are closed sets with many operations — sealed and switch. A plugin system or strategy set that third parties extend is open — interfaces and polymorphism. This also replaces most hand-written Visitor pattern code, with exhaustiveness checking the Visitor never had."

**Code:**

Partial illustrative snippet — `PaymentResult` and the services are assumed context:

```java
sealed interface PaymentResult permits Approved, Declined, PendingReview {}
record Approved(String txnId, Money amount) implements PaymentResult {}
record Declined(String reason, boolean retryable) implements PaymentResult {}
record PendingReview(String caseId) implements PaymentResult {}

// A new operation is a new method, not a change to three classes
HttpStatus toStatus(PaymentResult result) {
    return switch (result) {
        case Approved a -> HttpStatus.OK;
        case Declined(var reason, var retryable) when retryable -> HttpStatus.SERVICE_UNAVAILABLE;
        case Declined d -> HttpStatus.UNPROCESSABLE_ENTITY;
        case PendingReview p -> HttpStatus.ACCEPTED;
    };
}
```

**Follow-up:**

- *"Where does this go wrong?"* — When a 'closed' set isn't actually closed. If other teams need to add variants, sealing forces them to change your module, and you've built a bottleneck. Also, `default` branches in switches over sealed types throw away the exhaustiveness check — I'd flag them in code review.
- *"How does Jackson deserialize a sealed hierarchy?"* — Same as any polymorphic type: a type discriminator via `@JsonTypeInfo`/`@JsonSubTypes`. Sealing doesn't give the serializer the subtype list automatically unless the library version explicitly supports reading `permits`, so check your version rather than assuming.

**Source:** [JEP 409 — Sealed Classes](https://openjdk.org/jeps/409), [JEP 441 — Pattern Matching for switch](https://openjdk.org/jeps/441), [Brian Goetz — Data Oriented Programming in Java (InfoQ)](https://www.infoq.com/articles/data-oriented-programming-java/)

---

### 11. What Would You Check Before Upgrading a Spring Boot Service From Java 17 to 21?

**Answer:**

"I treat it as three separate changes and roll them out separately, so a regression points at one cause. **First, just the JDK**: bump the toolchain and base image, upgrade anything that does bytecode work (ASM, ByteBuddy, Mockito, Lombok, Jacoco, agents like APM tools) to versions that support class-file version 65, and run the full suite plus a soak test. **Second, GC**: if latency matters, try generational ZGC — on 21 it's opt-in with `-XX:+UseZGC -XX:+ZGenerational`. It became the default ZGC mode in JDK 23 and non-generational mode was removed in JDK 24. Compare pause times and CPU against G1 under real load. **Third, virtual threads**: turning on `spring.threads.virtual.enabled` changes the concurrency model, so before that I'd look for `synchronized` blocks around I/O (pinning on 21), large `ThreadLocal` caches, and connection pools that were implicitly protected by the Tomcat thread cap.

New language features — records, sealed types, pattern switch — I'd adopt gradually in new code, not as a big-bang refactor."

**Code:**

Shell command — opt-in flags on JDK 21:

```bash
# Generational ZGC on JDK 21 (opt-in; default ZGC mode from JDK 23)
java -XX:+UseZGC -XX:+ZGenerational -jar app.jar

# JDK 21: print a stack trace when a virtual thread pins its carrier while blocking
java -Djdk.tracePinnedThreads=full -jar app.jar
```

Configuration — Spring Boot 3.2+:

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

**Follow-up:**

- *"Virtual threads enabled and the DB falls over — why?"* — Before, 200 Tomcat threads meant at most about 200 requests competing for, say, a 20-connection Hikari pool. With virtual threads there's no such cap, so thousands of requests queue on the pool and hit `connectionTimeout`, or a downstream gets far more concurrent calls than it ever saw. The fix is an explicit limit — a bulkhead or a semaphore — at the resource, not a thread pool.
- *"How do you find pinning in production on 21?"* — JFR records a `jdk.VirtualThreadPinned` event when a virtual thread blocks while pinned beyond a threshold. That's the production-safe option; `jdk.tracePinnedThreads` is more of a dev/test tool.

**Source:** [JEP 439 — Generational ZGC](https://openjdk.org/jeps/439), [JEP 474 — ZGC: Generational Mode by Default](https://openjdk.org/jeps/474), [JEP 490 — ZGC: Remove the Non-Generational Mode](https://openjdk.org/jeps/490), [JEP 444 — Virtual Threads (pinning and JFR events)](https://openjdk.org/jeps/444)

---

## Applied: Resilience4j Configuration for a Downstream Dependency

The questions below walk through one concrete configuration for protecting a call to a single downstream (here, an entitlement service), setting by setting. The numbers are starting values to validate against the downstream's measured capacity and latency, not recommendations. For *why* the three patterns compose at the architecture level, see [Microservices Architecture Patterns Q14](../Microservices%20%26%20Architecture%20Patterns/Microservices_Architecture_Patterns_Interview_Prep.md#14-explain-circuit-breaker-bulkhead-and-retry-as-a-combined-resilience-strategy).

### 12. Walk Me Through Your Resilience4j Configuration for a Downstream Call

**Answer:**

"I configure four layers per downstream, each answering a different question. **Bulkhead**: how many calls can be in flight at once? **Rate limiter**: how many calls can *start* per second? **Circuit breaker**: is the dependency healthy enough to call at all? **Retry**: is this specific failure worth trying again? Each one has its own instance named after the dependency, so a problem with one downstream can't affect the limits on another."

**Code:**

Configuration — `application.yml`, Resilience4j Spring Boot 3 starter:

```yaml
resilience4j:
  bulkhead:
    instances:
      entitlementService:
        maxConcurrentCalls: 20        # max calls in flight at once
        maxWaitDuration: 500ms        # how long to wait for a free slot

  ratelimiter:
    instances:
      entitlementService:
        limitForPeriod: 50            # calls allowed per window
        limitRefreshPeriod: 1s        # window length
        timeoutDuration: 500ms        # how long to wait for a permit

  circuitbreaker:
    instances:
      entitlementService:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 20         # look at the last 20 calls
        minimumNumberOfCalls: 10      # need 10 calls before judging
        failureRateThreshold: 50      # open at 50% failures
        waitDurationInOpenState: 10s  # stay open 10s
        permittedNumberOfCallsInHalfOpenState: 5   # 5 trial calls
        ignoreExceptions:
          - com.example.EntitlementNotFoundException

  retry:
    instances:
      entitlementService:
        maxAttempts: 3
        waitDuration: 200ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        retryExceptions:
          - java.io.IOException
          - org.springframework.web.client.ResourceAccessException
        ignoreExceptions:
          - com.example.EntitlementNotFoundException
          - io.github.resilience4j.bulkhead.BulkheadFullException
          - io.github.resilience4j.ratelimiter.RequestNotPermitted
```

Partial illustrative snippet — `EntitlementClient` and `Entitlement` are assumed context:

```java
@Retry(name = "entitlementService", fallbackMethod = "fallback")
@CircuitBreaker(name = "entitlementService")
@RateLimiter(name = "entitlementService")
@Bulkhead(name = "entitlementService")
public Entitlement getEntitlement(String userId) {
    return entitlementClient.fetch(userId);
}

// Same parameters plus a Throwable, same return type
private Entitlement fallback(String userId, Throwable t) {
    return Entitlement.denyByDefault(userId);
}
```

**Follow-up:**

- *"Why is the fallback on `@Retry` and not `@CircuitBreaker`?"* — A fallback turns an exception into a normal return value at that layer. Put it on the circuit breaker, which sits *inside* retry, and retry never sees a failure, so it never retries. Put the fallback on the outermost layer.
- *"What's missing from this config?"* — Timeouts. Nothing here bounds how long a single call can take. Resilience4j's `TimeLimiter` only applies to asynchronous (`CompletionStage`/reactive) methods, so for a synchronous `RestClient`/`RestTemplate` call the timeout has to be set on the HTTP client (connect and read timeouts). Without it, a hung downstream holds a bulkhead slot indefinitely.

**Source:** [Resilience4j — Getting Started with Spring Boot 3](https://resilience4j.readme.io/docs/getting-started-3), [Resilience4j — TimeLimiter](https://resilience4j.readme.io/docs/timeout)

---

### 13. Explain the Bulkhead and Rate Limiter Settings — and Why You Need Both

**Answer:**

"**Bulkhead.** `maxConcurrentCalls: 20` means at most 20 calls to this dependency run at the same time. That's the compartment wall: if the downstream slows down, only 20 of my threads can be stuck on it, and everything else in the service keeps working. `maxWaitDuration: 500ms` means the 21st caller waits up to 500ms for a slot, then fails fast with `BulkheadFullException`. The default is 0 — fail immediately — and a short wait absorbs small bursts without letting requests queue indefinitely. I size it from what the downstream can handle, from load tests or its SLA, and on platform threads I keep it well below the Tomcat thread count.

**Rate limiter.** `limitForPeriod: 50` with `limitRefreshPeriod: 1s` means 50 calls per second, with permits refilled every second. `timeoutDuration: 500ms` means a call over the limit waits up to 500ms for the next refresh, then fails with `RequestNotPermitted`. The default wait is 5 seconds, which is far too long to hold a request thread, so I always set it.

They're different limits. The bulkhead caps how many calls *overlap in time*; the rate limiter caps how many *start per second*. Twenty fast calls can easily mean hundreds per second, which would blow through a contractual quota at an API gateway. Twenty slow calls might be only a few per second but still pile up. A quota-limited downstream needs the rate limiter; a slow one needs the bulkhead."

**Code:**

```text
Same 20-slot bulkhead, two downstream latencies:

  latency  50ms -> each slot completes ~20 calls/s -> up to ~400 calls/s  (bulkhead allows it, quota of 50/s does not)
  latency  2s   -> each slot completes ~0.5 calls/s -> ~10 calls/s        (rate limiter idle, bulkhead is the binding limit)

Concurrency ≈ throughput × latency (Little's Law), so each limit binds in a different regime.
```

**Follow-up:**

- *"Semaphore bulkhead or thread-pool bulkhead?"* — The annotation defaults to the semaphore bulkhead, which limits concurrency on the caller's own thread. `ThreadPoolBulkhead` (`type = Bulkhead.Type.THREADPOOL`) runs the call on a separate bounded pool and requires a `CompletableFuture`/`CompletionStage` return type. With virtual threads, the semaphore bulkhead is the natural choice. Virtual threads also remove the Tomcat-pool cap that used to limit outbound concurrency by accident, so the bulkhead becomes the only real limit.
- *"Rate limiting across 10 pods?"* — Resilience4j's rate limiter is per JVM. With 10 replicas at 50/s each, the downstream sees up to 500/s. Either divide the quota by the replica count, or enforce the limit centrally (API gateway, or a shared store like Redis).

**Source:** [Resilience4j — Bulkhead](https://resilience4j.readme.io/docs/bulkhead), [Resilience4j — RateLimiter](https://resilience4j.readme.io/docs/ratelimiter)

---

### 14. Explain the Circuit Breaker Settings and State Machine

**Answer:**

"The circuit breaker has three states. **Closed** is normal: calls flow through and outcomes are recorded. **Open**: calls are rejected immediately with `CallNotPermittedException`, so we stop hammering a dying service and give it room to recover. **Half-open**: after `waitDurationInOpenState` — 10 seconds here — it lets `permittedNumberOfCallsInHalfOpenState` (5) trial calls through. If the failure rate among those trials is below the threshold, it closes. If it's at or above, it reopens.

The settings: `slidingWindowSize: 20` with `COUNT_BASED` means it measures the failure rate over the last 20 calls. `minimumNumberOfCalls: 10` means it won't judge until it has seen 10 calls, so one failure out of the first two doesn't trip it. `failureRateThreshold: 50` opens it when 50% or more of the window failed. `ignoreExceptions` lists business errors like 'entitlement not found' — ignored exceptions count as *neither* failure nor success. Otherwise a burst of legitimate not-found responses could open the circuit on a perfectly healthy service."

**Code:**

```text
          failure rate >= 50%
          (after >= 10 calls in a 20-call window)
CLOSED  ------------------------------------------->  OPEN  (reject: CallNotPermittedException)
  ^                                                   |    ^
  |                                         after 10s |    | trial failure rate >= 50%
  |  trial failure rate < 50%                         v    |
  +-----------------------------------------------  HALF_OPEN  (allow 5 trial calls)
```

**Follow-up:**

- *"The downstream doesn't error, it just gets slow. Does this open?"* — Not with this config. Slow calls are tracked separately: `slowCallDurationThreshold` defaults to 60 seconds and `slowCallRateThreshold` to 100%, so in practice slowness never trips it. For a latency-sensitive dependency I'd set something like `slowCallDurationThreshold: 2s` and `slowCallRateThreshold: 50`.
- *"Why are defaults dangerous here?"* — Defaults are `slidingWindowSize: 100`, `minimumNumberOfCalls: 100`, and `waitDurationInOpenState: 60s`. On a low-traffic dependency, 100 calls can take minutes to accumulate, so the breaker reacts far too late.
- *"Count-based or time-based window?"* — Count-based reacts consistently per call. Time-based (`TIME_BASED`, size in seconds) is steadier when traffic varies a lot, because a quiet period doesn't leave stale outcomes in the window.

**Source:** [Resilience4j — CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker)

---

### 15. Explain the Retry Settings — What Do You Retry, and What Don't You?

**Answer:**

"`maxAttempts: 3` *includes* the first call, so that's 2 retries. `waitDuration: 200ms` with exponential backoff and multiplier 2 gives waits of about 200ms and then 400ms. Backoff avoids retrying instantly into a service that's already struggling. In production I'd add jitter so many clients don't retry in lockstep — Resilience4j supports a randomized wait, but check how your version combines it with exponential backoff.

`retryExceptions` is the allow-list: only transient failures like I/O errors and connection timeouts are retried. Once you set it, anything *not* on it isn't retried. `ignoreExceptions` is the explicit deny-list: business errors like 'not found' are never retried, because they'll fail the same way every time. I also list `BulkheadFullException` and `RequestNotPermitted` there. Retrying right after my own bulkhead or rate limiter rejected the call only adds pressure. Strictly speaking, they're already excluded by the allow-list. Listing them keeps that behavior if someone later widens `retryExceptions` or removes it."

**Code:**

```text
attempt 1  ──fail (IOException)──>  wait 200ms
attempt 2  ──fail (IOException)──>  wait 400ms   (200ms × 2)
attempt 3  ──fail──>                give up, fallback runs (maxAttempts = 3 includes attempt 1)

EntitlementNotFoundException  -> ignored: not retried, rethrown immediately
BulkheadFullException         -> ignored: retrying just re-hits the full bulkhead
CallNotPermittedException     -> not in retryExceptions, so not retried
```

**Follow-up:**

- *"Is retrying safe for every call?"* — Only for idempotent operations. A retried POST that timed out may already have succeeded downstream. Retry non-idempotent writes only with an idempotency key the downstream honors.
- *"How does retry interact with the circuit breaker's window?"* — Because retry is outside the circuit breaker, every attempt is recorded separately. One user request against a failing downstream contributes up to 3 failures, so the breaker trips about three times sooner in terms of *requests* than the threshold suggests. That's usually what you want, but account for it when picking `minimumNumberOfCalls`.
- *"Retries at several layers?"* — If the gateway retries 3×, the service retries 3×, and the HTTP client retries 3×, one user click becomes 27 downstream calls. Retry at one layer, ideally closest to the failure.

**Source:** [Resilience4j — Retry](https://resilience4j.readme.io/docs/retry), [AWS Builders' Library — Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

---

### 16. In What Order Do the Resilience4j Aspects Run, and Why Does It Matter?

**Answer:**

"With the Spring Boot starter, the default order is `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( Function ) ) ) ) )`. Retry is outermost and the bulkhead is innermost, right around the method. The order of the annotations on the method doesn't change this — the aspect-order properties do, like `resilience4j.retry.retryAspectOrder`.

That order is what makes the design hold together. Because retry is outermost, every retry attempt goes back through the circuit breaker, rate limiter, and bulkhead. Retries can't exceed the caps — concurrency stays at 20 and the rate at 50 per second, retries included. And once the circuit opens, retry attempts get `CallNotPermittedException` instantly instead of reaching the downstream."

**Code:**

```text
request
  └─ Retry                 (up to 3 attempts, backoff between them)
       └─ CircuitBreaker   (OPEN?  -> CallNotPermittedException, no call made)
            └─ RateLimiter (no permit within 500ms -> RequestNotPermitted)
                 └─ TimeLimiter (async methods only)
                      └─ Bulkhead (no slot within 500ms -> BulkheadFullException)
                           └─ entitlementClient.fetch(userId)
```

**Follow-up:**

- *"Should rate-limiter and bulkhead rejections count against the circuit breaker?"* — They do by default: they're thrown inside the breaker, so they're recorded as failures. Under heavy load, your own throttling can then open the circuit on a healthy downstream. If that's not what you want, add `BulkheadFullException` and `RequestNotPermitted` to the circuit breaker's `ignoreExceptions` as well.
- *"When would you change the order?"* — Rarely. The most common reason is wanting the circuit breaker to see only the final outcome of a retried call rather than each attempt, which means moving retry inside it. It's an unusual choice and should be a deliberate one.

**Source:** [Resilience4j — Getting Started with Spring Boot 3 (aspect order)](https://resilience4j.readme.io/docs/getting-started-3)

---

### 17. How Would You Summarize Your Resilience Setup in Under a Minute?

**Answer:**

"I protect a downstream like a slow legacy SOAP service in layers. The bulkhead caps concurrent calls at about 20, so a slow dependency can't take all our threads. The rate limiter keeps us inside the downstream's quota. The circuit breaker opens at 50% failures over a 20-call window and probes with 5 calls after 10 seconds. Business errors are ignored, so a burst of not-founds can't trip it. Retry sits outermost with 3 attempts and exponential backoff, only on transient exceptions — never on business errors, and never on our own bulkhead or rate-limiter rejections. Every call has a client-level timeout, and the fallback sits on the outermost layer. I'd tune all these numbers from load tests and APM latency percentiles, not guess them."

If asked *"why these numbers?"*: they're starting values, validated against the downstream's real capacity, its p99 latency, and its quota — and revisited when those change.

**Code:**

```text
Setting                         Value   Why
------------------------------  ------  -----------------------------------------------------------
bulkhead.maxConcurrentCalls     20      what the downstream sustains; well below request-thread count
bulkhead.maxWaitDuration        500ms   absorb small bursts, then fail fast
ratelimiter.limitForPeriod      50/1s   stay inside the downstream's quota (per pod)
circuitbreaker window / min     20 / 10 react quickly, but not on a handful of calls
circuitbreaker threshold        50%     clearly unhealthy, not a blip
circuitbreaker open wait        10s     give the downstream room to recover
retry.maxAttempts               3       2 retries, transient errors only, 200ms -> 400ms backoff
```

**Follow-up:**

> Personal example to add: describe a real incident where one of these settings (bulkhead size, circuit breaker threshold, or retry policy) was tuned after a production event, including context, decision, outcome, and lesson.

**Source:** [Resilience4j documentation](https://resilience4j.readme.io/docs/getting-started), [Michael Nygard — Release It! (2nd ed.)](https://pragprog.com/titles/mnee2/release-it-second-edition/)

---

## Sources & Further Reading — Consolidated

- [OpenJDK — JDK 21 project page and JEP list](https://openjdk.org/projects/jdk/21/)
- [JEP 395 — Records](https://openjdk.org/jeps/395) · [JEP 409 — Sealed Classes](https://openjdk.org/jeps/409) · [JEP 394 — Pattern Matching for instanceof](https://openjdk.org/jeps/394)
- [JEP 441 — Pattern Matching for switch](https://openjdk.org/jeps/441) · [JEP 440 — Record Patterns](https://openjdk.org/jeps/440) · [JEP 456 — Unnamed Variables & Patterns](https://openjdk.org/jeps/456)
- [JEP 431 — Sequenced Collections](https://openjdk.org/jeps/431) · [JEP 444 — Virtual Threads](https://openjdk.org/jeps/444) · [JEP 491 — Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491)
- [JEP 439 — Generational ZGC](https://openjdk.org/jeps/439) · [JEP 474](https://openjdk.org/jeps/474) · [JEP 490](https://openjdk.org/jeps/490)
- [Brian Goetz — Data Oriented Programming in Java](https://www.infoq.com/articles/data-oriented-programming-java/)
- [Resilience4j documentation](https://resilience4j.readme.io/docs/getting-started) — CircuitBreaker, Bulkhead, RateLimiter, Retry, TimeLimiter, Spring Boot 3 starter
- [AWS Builders' Library — Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
