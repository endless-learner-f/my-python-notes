class Student:
    # 1. 初始化办法:造人的时候自动带上名字，学号和全0的成绩单
    def __init__(self,name,student_id):
        self.name = name
        self.student_id = student_id
        self.grades = {"chinese": 0, "math": 0,"english": 0 }


    # 2. 设计成绩的方法
    def set_grade(self,course,grade):
        if course in self.grades:
            self.grades[course] = grade


    # 3. 打印成绩的方法
    def print_grades(self):
        print(f"学生{self.name} (学号；{self.student_id})的成绩为:")
        for course  in self.grades:
            print(f"{course}:{self.grades[course]}")


# 4. 实例化: 照着图纸造两个学生
chen = Student("小陈","100618")
zeng = Student("小曾","100622")


# 5. 叫小陈去改成绩，并打印出来
chen.set_grade("chinese", 92)
chen.set_grade("math",94)
chen.print_grades()
