package source;

import java.util.Date;

public class Visit {
    private Integer id;
    private Date date;
    private String description;
    private Pet pet;

    // Getters and setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public Date getDate() { return date; }
    public void setDate(Date date) { this.date = date; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public Pet getPet() { return pet; }
    public void setPet(Pet pet) { this.pet = pet; }
}