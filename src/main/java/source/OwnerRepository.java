package source;

import java.util.Collection;

public interface OwnerRepository {
    Collection<Owner> findAll();
    Owner findById(Integer id);
    void save(Owner owner);
    void delete(Owner owner);
    Collection<Owner> findByLastName(String lastName);
}

// Similar interfaces for PetRepository, VetRepository, etc.