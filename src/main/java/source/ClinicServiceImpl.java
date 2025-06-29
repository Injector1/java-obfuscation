/*
 * Copyright 2002-2017 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package source;

import java.util.Collection;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.dao.DataAccessException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.orm.ObjectRetrievalFailureException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Mostly used as a facade for all Petclinic controllers
 * Also a placeholder for @Transactional and @Cacheable annotations
 *
 * @author Michael Isvy
 * @author Vitaliy Fedoriv
 */
@Service
public class ClinicServiceImpl implements ClinicService {

    private PetRepository petRepository;
    private VetRepository vetRepository;
    private OwnerRepository ownerRepository;
    private VisitRepository visitRepository;
    private SpecialtyRepository specialtyRepository;
    private PetTypeRepository petTypeRepository;

    /**
     * Constructs a new ClinicServiceImpl with all required repositories.
     *
     * @param petRepository Repository for Pet entities
     * @param vetRepository Repository for Vet entities
     * @param ownerRepository Repository for Owner entities
     * @param visitRepository Repository for Visit entities
     * @param specialtyRepository Repository for Specialty entities
     * @param petTypeRepository Repository for PetType entities
     */
    @Autowired
    public ClinicServiceImpl(
            PetRepository petRepository,
            VetRepository vetRepository,
            OwnerRepository ownerRepository,
            VisitRepository visitRepository,
            SpecialtyRepository specialtyRepository,
            PetTypeRepository petTypeRepository) {
        this.petRepository = petRepository;
        this.vetRepository = vetRepository;
        this.ownerRepository = ownerRepository;
        this.visitRepository = visitRepository;
        this.specialtyRepository = specialtyRepository;
        this.petTypeRepository = petTypeRepository;
    }

    /**
     * Retrieves all pets from the system.
     *
     * @return A Collection of all Pet entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Pet> findAllPets() throws DataAccessException {
        return petRepository.findAll();
    }

    /**
     * Deletes the specified pet from the system.
     *
     * @param pet The Pet entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deletePet(Pet pet) throws DataAccessException {
        petRepository.delete(pet);
    }

    /**
     * Finds a visit by its ID.
     *
     * @param visitId The ID of the visit to find
     * @return The found Visit entity, or null if no visit is found
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Visit findVisitById(int visitId) throws DataAccessException {
        Visit visit = null;
        try {
            visit = visitRepository.findById(visitId);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return visit;
    }

    /**
     * Retrieves all visits from the system.
     *
     * @return A Collection of all Visit entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Visit> findAllVisits() throws DataAccessException {
        return visitRepository.findAll();
    }

    /**
     * Deletes the specified visit from the system.
     *
     * @param visit The Visit entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deleteVisit(Visit visit) throws DataAccessException {
        visitRepository.delete(visit);
    }

    /**
     * Finds a vet by its ID.
     *
     * @param id The ID of the vet to find
     * @return The found Vet entity, or null if no vet is found
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Vet findVetById(int id) throws DataAccessException {
        Vet vet = null;
        try {
            vet = vetRepository.findById(id);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return vet;
    }

    /**
     * Retrieves all vets from the system.
     *
     * @return A Collection of all Vet entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Vet> findAllVets() throws DataAccessException {
        return vetRepository.findAll();
    }

    /**
     * Saves a vet to the system. Will update an existing vet or create a new one.
     *
     * @param vet The Vet entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void saveVet(Vet vet) throws DataAccessException {
        vetRepository.save(vet);
    }

    /**
     * Deletes the specified vet from the system.
     *
     * @param vet The Vet entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deleteVet(Vet vet) throws DataAccessException {
        vetRepository.delete(vet);
    }

    /**
     * Retrieves all owners from the system.
     *
     * @return A Collection of all Owner entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Owner> findAllOwners() throws DataAccessException {
        return ownerRepository.findAll();
    }

    /**
     * Deletes the specified owner from the system.
     *
     * @param owner The Owner entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deleteOwner(Owner owner) throws DataAccessException {
        ownerRepository.delete(owner);
    }

    /**
     * Finds a pet type by its ID.
     *
     * @param petTypeId The ID of the pet type to find
     * @return The found PetType entity, or null if no pet type is found
     */
    @Override
    @Transactional(readOnly = true)
    public PetType findPetTypeById(int petTypeId) {
        PetType petType = null;
        try {
            petType = petTypeRepository.findById(petTypeId);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return petType;
    }

    /**
     * Retrieves all pet types from the system.
     *
     * @return A Collection of all PetType entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<PetType> findAllPetTypes() throws DataAccessException {
        return petTypeRepository.findAll();
    }

    /**
     * Saves a pet type to the system. Will update an existing pet type or create a new one.
     *
     * @param petType The PetType entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void savePetType(PetType petType) throws DataAccessException {
        petTypeRepository.save(petType);
    }

    /**
     * Deletes the specified pet type from the system.
     *
     * @param petType The PetType entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deletePetType(PetType petType) throws DataAccessException {
        petTypeRepository.delete(petType);
    }

    /**
     * Finds a specialty by its ID.
     *
     * @param specialtyId The ID of the specialty to find
     * @return The found Specialty entity, or null if no specialty is found
     */
    @Override
    @Transactional(readOnly = true)
    public Specialty findSpecialtyById(int specialtyId) {
        Specialty specialty = null;
        try {
            specialty = specialtyRepository.findById(specialtyId);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return specialty;
    }

    /**
     * Retrieves all specialties from the system.
     *
     * @return A Collection of all Specialty entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Specialty> findAllSpecialties() throws DataAccessException {
        return specialtyRepository.findAll();
    }

    /**
     * Saves a specialty to the system. Will update an existing specialty or create a new one.
     *
     * @param specialty The Specialty entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void saveSpecialty(Specialty specialty) throws DataAccessException {
        specialtyRepository.save(specialty);
    }

    /**
     * Deletes the specified specialty from the system.
     *
     * @param specialty The Specialty entity to be deleted
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void deleteSpecialty(Specialty specialty) throws DataAccessException {
        specialtyRepository.delete(specialty);
    }

    /**
     * Retrieves all pet types from the system.
     *
     * @return A Collection of all PetType entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<PetType> findPetTypes() throws DataAccessException {
        return petRepository.findPetTypes();
    }

    /**
     * Finds an owner by its ID.
     *
     * @param id The ID of the owner to find
     * @return The found Owner entity, or null if no owner is found
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Owner findOwnerById(int id) throws DataAccessException {
        Owner owner = null;
        try {
            owner = ownerRepository.findById(id);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return owner;
    }

    /**
     * Finds a pet by its ID.
     *
     * @param id The ID of the pet to find
     * @return The found Pet entity, or null if no pet is found
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Pet findPetById(int id) throws DataAccessException {
        Pet pet = null;
        try {
            pet = petRepository.findById(id);
        } catch (ObjectRetrievalFailureException|EmptyResultDataAccessException e) {
            // just ignore not found exceptions for Jdbc/Jpa realization
            return null;
        }
        return pet;
    }

    /**
     * Saves a pet to the system. Will update an existing pet or create a new one.
     *
     * @param pet The Pet entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void savePet(Pet pet) throws DataAccessException {
        petRepository.save(pet);

    }

    /**
     * Saves a visit to the system. Will update an existing visit or create a new one.
     *
     * @param visit The Visit entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void saveVisit(Visit visit) throws DataAccessException {
        visitRepository.save(visit);

    }

    /**
     * Retrieves all vets from the system.
     *
     * @return A Collection of all Vet entities in the system
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    @Cacheable(value = "vets")
    public Collection<Vet> findVets() throws DataAccessException {
        return vetRepository.findAll();
    }

    /**
     * Saves an owner to the system. Will update an existing owner or create a new one.
     *
     * @param owner The Owner entity to save
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional
    public void saveOwner(Owner owner) throws DataAccessException {
        ownerRepository.save(owner);

    }

    /**
     * Finds owners by their last name.
     *
     * @param lastName The last name of the owner to find
     * @return A Collection of Owner entities matching the last name
     * @throws DataAccessException If an error occurs while accessing the data
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Owner> findOwnerByLastName(String lastName) throws DataAccessException {
        return ownerRepository.findByLastName(lastName);
    }

    /**
     * Finds visits by the pet's ID.
     *
     * @param petId The ID of the pet whose visits are to be found
     * @return A Collection of Visit entities associated with the specified pet ID
     */
    @Override
    @Transactional(readOnly = true)
    public Collection<Visit> findVisitsByPetId(int petId) {
        return visitRepository.findByPetId(petId);
    }
}
