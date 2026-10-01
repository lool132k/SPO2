using System;

class Program {
    static string AgeGroup(int age) {
        string group;
        if (age < 13) group = "Ребёнок";
        else if (age < 18) group = "Подросток";
        else if (age < 65) group = "Взрослый";
        else group = "Пенсионер";
        return group;
    }

    static int SumEven(int[] numbers) {
        int total = 0;
        for (int i = 0; i < numbers.Length; i++)
            if (numbers[i] % 2 == 0) total += numbers[i];
        return total;
    }

    static int CountLong(string[] words) {
        int count = 0;
        foreach (string w in words)
            if (w.Length > 5) count++;
        return count;
    }

    static void PrintSquares(int n) {
        while (n > 0) { Console.WriteLine(n * n); n--; }
    }

    static int DigitCount(int number) {
        int count = 0;
        do { count++; number /= 10; } while (number > 0);
        return count;
    }

    static string QuarterName(int q) {
        string name;
        switch (q) {
            case 1: name = "Первый"; break;
            case 2: name = "Второй"; break;
            case 3: name = "Третий"; break;
            default: name = "Четвёртый"; break;
        }
        return name;
    }

    static void Main() {
        Console.WriteLine(AgeGroup(25));
        Console.WriteLine(QuarterName(2));
    }
}