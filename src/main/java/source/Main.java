package source;

//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
public class Main {
    public static void main(String[] args) {
        //TIP Press <shortcut actionId="ShowIntentionActions"/> with your caret at the highlighted text
        // to see how IntelliJ IDEA suggests fixing it.
        System.out.printf("Hello and welcome!");
    }

    /**
     * Addition method that takes two integers and returns their sum.
     * @param a - the first integer
     * @param b - the second integer
     * @return the sum of a and b
     */
    public static int add(int a, int b) {
        return a + b;
    }

    /**
     * Subtraction method that takes two integers and returns their difference.
     * @param a - the first integer
     * @param b - the second integer
     * @return the difference of a and b
     */
    public static int subtract(int a, int b) {
        return a - b;
    }

    /**
     * Multiplication method that takes two integers and returns their product.
     * @param a - the first integer
     * @param b - the second integer
     * @return the product of a and b
     */
    public static int multiply(int a, int b) {
        return a * b;
    }

    /**
     * Division method that takes two integers and returns their quotient.
     * Throws an ArithmeticException if the second integer is zero.
     * @param a - the numerator
     * @param b - the denominator
     * @return the quotient of a and b
     */
    public static double divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return (double) a / b;
    }

    /**
     * Sorts an array of integers using the bubble sort algorithm.
     *
     * @param array - the array to be sorted
     * @return the sorted array
     */
    public static int[] bubbleSort(int[] array) {
        int n = array.length;
        boolean swapped;
        do {
            swapped = false;
            for (int i = 0; i < n - 1; i++) {
                if (array[i] > array[i + 1]) {
                    int temp = array[i];
                    array[i] = array[i + 1];
                    array[i + 1] = temp;
                    swapped = true;
                }
            }
            n--;
        } while (swapped);
        return array;
    }
}