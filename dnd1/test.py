import requests

external_url = "http://localhost:7000"

json_params = {'campaign_id': ['45'], 'player_id': ['88']}
resp1 = requests.post(external_url+'/game', json=json_params)
# HTML с встроенным скриптом для отправки данных
html_content = f"""
    <html>
        <body>
            <h1>Redirecting...</h1>
            <form id="redirectForm" action="{external_url}" method="POST">
                <input type="hidden" name="user_data" value='{json_params}' />
            </form>
            <script type="text/javascript">
                // Автоматически отправляем форму после загрузки страницы
                document.getElementById('redirectForm').submit();
            </script>
        </body>
    </html>
    """
