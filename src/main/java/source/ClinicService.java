package source;

import java.util.Collection;
import org.springframework.dao.DataAccessException;

public interface ClinicService {
    Collection<Pet> findAllPets() throws DataAccessException;
    void deletePet(Pet pet) throws DataAccessException;
    Visit findVisitById(int visitId) throws DataAccessException;
    Collection<Visit> findAllVisits() throws DataAccessException;
    void deleteVisit(Visit visit) throws DataAccessException;
    Vet findVetById(int id) throws DataAccessException;
    Collection<Vet> findAllVets() throws DataAccessException;
    void saveVet(Vet vet) throws DataAccessException;
    void deleteVet(Vet vet) throws DataAccessException;
    Collection<Owner> findAllOwners() throws DataAccessException;
    void deleteOwner(Owner owner) throws DataAccessException;
    PetType findPetTypeById(int petTypeId);
    Collection<PetType> findAllPetTypes() throws DataAccessException;
    void savePetType(PetType petType) throws DataAccessException;
    void deletePetType(PetType petType) throws DataAccessException;
    Specialty findSpecialtyById(int specialtyId);
    Collection<Specialty> findAllSpecialties() throws DataAccessException;
    void saveSpecialty(Specialty specialty) throws DataAccessException;
    void deleteSpecialty(Specialty specialty) throws DataAccessException;
    Collection<PetType> findPetTypes() throws DataAccessException;
    Owner findOwnerById(int id) throws DataAccessException;
    Pet findPetById(int id) throws DataAccessException;
    void savePet(Pet pet) throws DataAccessException;
    void saveVisit(Visit visit) throws DataAccessException;
    Collection<Vet> findVets() throws DataAccessException;
    void saveOwner(Owner owner) throws DataAccessException;
    Collection<Owner> findOwnerByLastName(String lastName) throws DataAccessException;
    Collection<Visit> findVisitsByPetId(int petId);
}