package source;

import java.util.Date;

public class Pet {
    private Integer id;
    private String name;
    private Date birthDate;
    private PetType type;
    private Owner owner;

    // Getters and setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Date getBirthDate() { return birthDate; }
    public void setBirthDate(Date birthDate) { this.birthDate = birthDate; }

    public PetType getType() { return type; }
    public void setType(PetType type) { this.type = type; }

    public Owner getOwner() { return owner; }
    public void setOwner(Owner owner) { this.owner = owner; }
}