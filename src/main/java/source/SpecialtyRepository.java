package source;

import java.util.Collection;

public interface SpecialtyRepository {
    Collection<Specialty> findAll();
    Specialty findById(Integer id);
    void save(Specialty specialty);
    void delete(Specialty specialty);
}