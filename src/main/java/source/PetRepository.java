package source;

import java.util.Collection;

public interface PetRepository {
    Collection<Pet> findAll();
    Pet findById(Integer id);
    void save(Pet pet);
    void delete(Pet pet);
    Collection<PetType> findPetTypes();
}