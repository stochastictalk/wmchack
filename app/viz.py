# -*- utf-8 -*-

# Created: 9th November 2020
# Author: Jerome Wynne (jeromewynne@das-ltd.co.uk)
# Environment: wmchack
# Summary: visualizations for app.py

import analysis as an

def plot_cdf_of_file_lengths(data):
    reader = data['reader']
    x, P_x = an.cdf(file_lengths(reader))
    df_tmp = pd.DataFrame(data={'Words in file':x, 'Files with less than this many words':P_x})
    gobj = px.line(data_frame=df_tmp, x='Words in file',
                   y='Files with less than this many words')
    return gobj