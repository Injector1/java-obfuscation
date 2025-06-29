package source;

import java.util.Collection;

public interface VetRepository {
    Collection<Vet> findAll();
    Vet findById(Integer id);
    void save(Vet vet);
    void delete(Vet vet);
}