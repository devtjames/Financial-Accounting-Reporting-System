# Technical Decisions

## Structured Financial Records

The system uses structured records to:

- Ensure consistency in transaction storage  
- Enable accurate reporting  
- Simplify financial tracking over time  

---

## Centralized Database

A centralized database was used to:

- Maintain a single source of truth  
- Prevent data duplication  
- Enable reliable reporting and auditing  

---

## Server-Side Processing (PHP)

PHP was used for backend logic to:

- Handle financial calculations  
- Process and validate transactions  
- Maintain control over data flow  

---

## Relational Database (MySQL)

MySQL was selected because:

- It supports structured financial data  
- Enables relationships between accounts and transactions  
- Provides reliable query performance  

---

## Data Accuracy Approach

The system ensures correctness by:

- Validating all inputs before storage  
- Calculating balances from stored transactions  
- Preserving historical records  
- Preventing direct manipulation of computed values  

---

## Known Limitations

- Designed for small to medium-scale usage  
- Limited to core accounting features  
- No external integrations (e.g., banking APIs)  

These constraints were accepted based on the project scope.
