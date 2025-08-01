# Seeded Bugs

This document describes the intentional bugs that have been seeded into the original code for testing purposes. These bugs are designed to test the effectiveness of LLM-based test generation in detecting issues in both original and obfuscated code.

## Bug 1: Incomplete Exception Handling in findVisitById

**Location**: `ClinicServiceImpl.java` - `findVisitById` method

**Description**: The exception handling has been modified to catch only one exception type instead of both expected exceptions.

**Code Change**:
```java
try {
    visit = visitRepository.findById(visitId);
} catch (ObjectRetrievalFailureException e) {
    // Remove EmptyResultDataAccessException handling
    return null;
}
```

**Impact**: This bug removes proper handling of `EmptyResultDataAccessException`, which could lead to unhandled exceptions when the repository fails to find a visit with the specified ID.

## Bug 2: Wrong Repository Method Call in findPetTypes

**Location**: `ClinicServiceImpl.java` - `findPetTypes` method

**Description**: The method calls the wrong repository method, using a generic `findAll()` instead of the correct domain-specific method.

**Code Change**:
```java
@Override
public Collection<PetType> findPetTypes() throws DataAccessException {
    return petTypeRepository.findAll(); // Should be petRepository.findPetTypes()
}
```

**Impact**: This bug causes the method to call an incorrect repository method, which may return wrong data or cause runtime errors depending on the repository implementation.
