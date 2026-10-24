# 这是定义函数。def  = define （定义）。参数是 weight (体重）和 height (身高)
def calculate_BMI(weight,height):


    #核心公式 **在 python 里面代表“次方”。  也就是体重 / （身高 *身高）
    BMI = weight / height ** 2


    #下面根据算出来的 BMI 进行分类判断
    if BMI <= 18.5:
        category = "偏瘦"
    elif BMI <= 25:
        category = "正常"
    elif BMI <= 30:
        category = "偏肥"
    else:
        category = "肥胖"


    # f-string (格式化字符串)。非常实用！直接在字符串前面加个 f，就能把变量塞进大括号里
    print(f"您的BMI分类为: {category}")


    # 把算出来的  BMI 值丢出去。谁调用这个函数，谁就能拿到这个结果
    return BMI


# 调用这个函数。传入 1.8 (身高) 和 70 (体重)。根据公式计算并打印，但这里没有用变量接收返回值
calculate_BMI(70, 1.8)

# 拿个盆（my_bmi）去接住函数的返回值
my_bmi = calculate_BMI(70, 1.8)

# 看看接住的具体数值是多少
print("接住的具体数值是：", my_bmi)