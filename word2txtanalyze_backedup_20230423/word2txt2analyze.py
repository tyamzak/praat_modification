import os
import docx
import subprocess


#######################################################################################
# このプログラムは、指定されたフォルダ内にあるWordファイルからテキストを抽出し、
# それを自動評価ツールにかけて得られた結果を集約し、Excelファイルに出力するプログラムです。
# 以下に各部分の説明を示します。
#######################################################################################
# input_folder_pathはWordファイルが格納されているフォルダのパス、
# tmp_folder_pathはテキストファイルを一時的に格納するフォルダのパス、
# output_folder_pathは自動評価ツールにかけた結果を格納するフォルダのパスを指定しています。
#######################################################################################

# フォルダのパスを指定する
input_folder_path = 'WordFiles'
tmp_folder_path = 'tmpFiles'
output_folder_path = 'output'


#######################################################################################
# この部分は、事前にoutput_folder_pathが空であることを確認するためのものです。
# プログラム実行前にoutput_folder_path内のファイルをすべて削除しておく必要があります。
#######################################################################################

# outputが空であることの確認
print('Is output directory empty?')

#yesが入力された場合、処理を実行します
if input('Type your answer : yes or else  ') == 'yes':
    pass
else:
    print('Be sure to remove all files from output directory before execution')
    exit()


#######################################################################################
# input_folder_path内のWordファイルからテキストを抽出し、tmp_folder_path内にテキストファイルを作成します。
#######################################################################################

#output_folderを作成する
result = subprocess.run(['mkdir', f'{tmp_folder_path}'], capture_output=True, text=True)
print(result.stdout)

# フォルダ内のdocxファイルに対して、テキストを抽出する
for filename in os.listdir(input_folder_path):
    
    if filename.endswith('.docx'):
        # Wordファイルを開く
        doc = docx.Document(os.path.join(input_folder_path, filename))

        # 各段落のテキストを抽出する
        text = []
        for para in doc.paragraphs:
            text.append(para.text)

        # テキストファイルに書き込む
        text_filename = os.path.splitext(filename)[0] + '.txt'
        with open(os.path.join(tmp_folder_path, text_filename), 'w', encoding='utf-8') as f:
            f.write('\n'.join(text))

#######################################################################################
# tmp_folder_path内のテキストファイルを1つずつ自動評価ツールにかけます。
#######################################################################################

for filename in os.listdir(tmp_folder_path):

    #autograderにひとつずつかけていく
    result = subprocess.run(['python3', './main.py', os.path.join(tmp_folder_path,filename)], capture_output=True, text=True)
    print(result.stdout)

#######################################################################################
#tmp_folderを削除する
#######################################################################################
result = subprocess.run(['rm', '-r', f'{tmp_folder_path}'], capture_output=True, text=True)
print(result.stdout)


#######################################################################################
# output_folder_path内のCSVファイルから結果を集約し、Excelファイルに出力します。
# pandasライブラリを用いてデータフレームを作成し、ファイル名からID、RN、Dateを
# 生成してカラムに追加しています。最後に、to_excelメソッドを用いてExcelファイル
# に出力しています。
#######################################################################################

#合計用のdfを作成
import pandas as pd

headers = ['filename','ID','RECN','Date','MN','wordtypes','swordtypes','lextypes','slextypes','wordtokens'
,'swordtokens','lextokens','slextokens','ld','ls1','ls2','vs1','vs2'
,'cvs1','ndw','ndwz','ndwerz','ndwesz','ttr','msttr','cttr','rttr'
,'logttr','uber','vv1','svv1','cvv1','lv','vv2','nv','adjv','advv','modv'
,'D','w','s','vp','c','t','dc','ct','cp','cn','MLS','MLT','MLC','C/S'
,'VP/T','C/T','DC/C','DC/T','T/S','CT/T','CP/T','CP/C','CN/T','CN/C']

masterdf = pd.DataFrame(columns= headers)

for filename in os.listdir(output_folder_path):

    df = pd.read_csv( os.path.join(output_folder_path,filename))
    masterdf = pd.concat([masterdf,df])


masterdf.loc[:,'ID'] =  masterdf.loc[:,'filename'].str[0:3]
masterdf.loc[:,'RECN'] =  masterdf.loc[:,'filename'].str[3:6]
masterdf.loc[:,'Date'] =  "20" + masterdf.loc[:,'filename'].str[6:8] + "-" + masterdf.loc[:,'filename'].str[8:10] + "-" + masterdf.loc[:,'filename'].str[10:12]
masterdf['MN'] = masterdf.index + 1
masterdf.to_excel('masterresult.xlsx',index=False)
print('finish')