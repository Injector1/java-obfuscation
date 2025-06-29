package source;

import java.util.Collection;

public interface VisitRepository {
    Collection<Visit> findAll();
    Visit findById(Integer id);
    void save(Visit visit);
    void delete(Visit visit);
    Collection<Visit> findByPetId(Integer petId);
}