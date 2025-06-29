package source;

import java.util.HashSet;
import java.util.Set;

public class Vet {
    private Integer id;
    private String firstName;
    private String lastName;
    private Set<Specialty> specialties = new HashSet<>();

    // Getters and setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public Set<Specialty> getSpecialties() { return specialties; }
    public void setSpecialties(Set<Specialty> specialties) { this.specialties = specialties; }
}