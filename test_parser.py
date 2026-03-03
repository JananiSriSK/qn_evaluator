"""Test PDF parser with sample text"""
import sys
sys.path.append('backend')

from services.pdf_parser import PDFQuestionParser

# Your exact PDF text
sample_text = """JAVA PROGRAMMING
MODEL QUESTION PAPER
Part A – Short Answer (10 × 2 = 20 Marks)
1. What is inheritance in Java and explain its types with suitable examples.
2. Compare method overloading and method overriding with examples.
3. Describe the role of interfaces in achieving abstraction.
4. Explain the difference between AWT and Swing components.
5. Explain file handling in Java and describe the different types of streams.
6. Explain how object serialization works in Java.
7. Define JSON and explain its role in web applications.
8. Describe the Servlet lifecycle.
9. Explain the concept of session tracking in web applications.
10. Define Hibernate ORM and mention its advantages.
Part B – Analytical / Application (5 × 10 = 50 Marks)
11. Explain classes, objects, inheritance, polymorphism, and exception handling with suitable
examples.
12. Write a Java program to demonstrate communication using DatagramSocket and
DatagramPacket. Explain the working process.
13. Design a simple GUI-based application using Swing that performs user input validation using
regular expressions. Explain the event handling mechanism used.
14. Explain JDBC architecture and develop a program to perform CRUD operations on a database
table. Analyze how multitier architecture improves scalability.
15. Explain Servlets and JSP in detail. Compare GenericServlet and HttpServlet. Illustrate session
tracking methods with examples.
16. Explain AJAX-based rich internet applications using JSON. Describe how Java Mail API
supports SMTP, POP3, and IMAP.
17. Explain Hibernate architecture. Demonstrate entity mapping using annotations and write sample
HQL queries.
18. Discuss Spring Framework and explain how MVC architecture is implemented using Spring.
Part C – Design / Evaluation (2 × 15 = 30 Marks)
19. (a) Design a distributed web-based student management system using Servlets, JSP, JDBC,
and MVC architecture. Justify the architectural choices.
OR
19. (b) Design a client-server application using Java networking (URLs, sockets, datagrams,
multicasting). Evaluate the advantages and limitations of each communication method.
20. (a) Design an enterprise application using Hibernate and Spring Framework. Explain O/R
mapping, dependency injection, and transaction management with appropriate diagrams.
OR
20. (b) Develop a case study illustrating integration of JSON, AJAX, and backend database
connectivity in a multitier web application. Evaluate performance considerations."""

# Parse
questions = PDFQuestionParser.split_questions(sample_text)

# Print results
print(f"\n{'='*80}")
print(f"TOTAL QUESTIONS PARSED: {len(questions)}")
print(f"{'='*80}\n")

for q in questions:
    print(f"Q{q['number']:>3} | {q['part']:7} | {q['text'][:60]}...")

# Check specific questions
print(f"\n{'='*80}")
print("CRITICAL CHECKS:")
print(f"{'='*80}")
print(f"Q10 Part: {[q for q in questions if q['number'] == '10'][0]['part']} (Expected: Part A)")
print(f"Q11 Part: {[q for q in questions if q['number'] == '11'][0]['part']} (Expected: Part B)")
q19_list = [q for q in questions if q['number'].startswith('19')]
if q19_list:
    print(f"Q19 Part: {q19_list[0]['part']} (Expected: Part C)")
print(f"\n[PASS] ALL CHECKS PASSED!" if all([
    [q for q in questions if q['number'] == '10'][0]['part'] == 'Part A',
    [q for q in questions if q['number'] == '11'][0]['part'] == 'Part B',
    q19_list and q19_list[0]['part'] == 'Part C'
]) else "\n[FAIL] CHECKS FAILED!")
