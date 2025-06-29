package source;

import java.util.Collection;

public interface PetTypeRepository {
    Collection<PetType> findAll();
    PetType findById(Integer id);
    void save(PetType petType);
    void delete(PetType petType);
}